// Thin promise wrapper around amazon-cognito-identity-js (sign up / confirm / sign in / sign out).
import {
  AuthenticationDetails,
  CognitoAccessToken,
  CognitoIdToken,
  CognitoRefreshToken,
  CognitoUser,
  CognitoUserAttribute,
  CognitoUserPool,
  CognitoUserSession,
} from 'amazon-cognito-identity-js';
import { getConfig } from './config.js';

let pool = null;
function userPool() {
  if (!pool) {
    const { userPoolId, userPoolClientId } = getConfig();
    pool = new CognitoUserPool({ UserPoolId: userPoolId, ClientId: userPoolClientId });
  }
  return pool;
}

const cognitoUser = (email) => new CognitoUser({ Username: email, Pool: userPool() });

export function isAllowedEmail(email) {
  const domain = getConfig().allowedEmailDomain;
  const parts = email.trim().toLowerCase().split('@');
  return parts.length === 2 && parts[1] === domain;
}

// Turns Cognito errors into messages a student understands.
export function friendlyError(err) {
  const msg = err?.message || String(err);
  const domain = getConfig().allowedEmailDomain;
  if (msg.includes('EMAIL_DOMAIN_NOT_ALLOWED'))
    return `Реєстрація можлива лише з університетською поштою @${domain}.`;
  if (msg.includes('EMAIL_BANNED'))
    return 'Акаунт з цією поштою заблоковано модератором. Якщо це помилка, напишіть адміністраторам ReadCycle.';
  if (msg.includes('EMAIL_USES_GOOGLE'))
    return 'Ця пошта вже входить через Google. Натисніть «Продовжити з Google».';
  if (msg.includes('EMAIL_NOT_VERIFIED'))
    return 'Google не підтвердив цю пошту. Скористайтеся підтвердженим акаунтом Google.';
  switch (err?.code) {
    case 'UsernameExistsException':
      return 'Користувач з цією поштою вже існує.';
    case 'CodeMismatchException':
      return 'Невірний код підтвердження.';
    case 'ExpiredCodeException':
      return 'Код застарів. Надішліть новий.';
    case 'NotAuthorizedException':
      return 'Невірна пошта або пароль.';
    case 'UserNotConfirmedException':
      return 'Пошту ще не підтверджено. Введіть код з листа.';
    case 'InvalidPasswordException':
      return 'Пароль: мінімум 8 символів, малі літери та цифри.';
    case 'LimitExceededException':
      return 'Забагато спроб. Спробуйте пізніше.';
    default:
      return msg;
  }
}

export function signUp(email, password) {
  return new Promise((resolve, reject) => {
    const attrs = [new CognitoUserAttribute({ Name: 'email', Value: email })];
    userPool().signUp(email, password, attrs, null, (err, res) =>
      err ? reject(err) : resolve(res),
    );
  });
}

export function confirmSignUp(email, code) {
  return new Promise((resolve, reject) => {
    cognitoUser(email).confirmRegistration(code, true, (err, res) =>
      err ? reject(err) : resolve(res),
    );
  });
}

export function resendCode(email) {
  return new Promise((resolve, reject) => {
    cognitoUser(email).resendConfirmationCode((err, res) => (err ? reject(err) : resolve(res)));
  });
}

// Password reset: Cognito emails a code, then the user sets a new password with it.
export function forgotPassword(email) {
  return new Promise((resolve, reject) => {
    cognitoUser(email).forgotPassword({ onSuccess: resolve, onFailure: reject });
  });
}

export function resetPassword(email, code, newPassword) {
  return new Promise((resolve, reject) => {
    cognitoUser(email).confirmPassword(code, newPassword, {
      onSuccess: resolve,
      onFailure: reject,
    });
  });
}

export function signIn(email, password) {
  return new Promise((resolve, reject) => {
    const details = new AuthenticationDetails({ Username: email, Password: password });
    cognitoUser(email).authenticateUser(details, {
      onSuccess: resolve,
      onFailure: reject,
    });
  });
}

// ---------- Sign in with Google (Cognito hosted UI, authorization code + PKCE) ----------
// Cognito talks to Google; we only redirect there and exchange the returned code for tokens.
// The tokens are then stored the same way amazon-cognito-identity-js stores its own sign-in,
// so getSession / getIdToken / signOut work unchanged for both kinds of login.

export const googleEnabled = () => Boolean(getConfig().cognitoDomain);

const STATE_KEY = 'rc_oauth_state';
const VERIFIER_KEY = 'rc_oauth_verifier';

const redirectUri = () => `${window.location.origin}/auth/callback`;

function base64url(bytes) {
  return btoa(String.fromCharCode(...new Uint8Array(bytes)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

const randomString = (bytes) => base64url(crypto.getRandomValues(new Uint8Array(bytes)));

export async function startGoogleSignIn() {
  const { cognitoDomain, userPoolClientId } = getConfig();
  const verifier = randomString(48);
  const state = randomString(16);
  sessionStorage.setItem(VERIFIER_KEY, verifier);
  sessionStorage.setItem(STATE_KEY, state);
  const challenge = base64url(
    await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier)),
  );
  const params = new URLSearchParams({
    response_type: 'code',
    client_id: userPoolClientId,
    redirect_uri: redirectUri(),
    scope: 'openid email profile',
    identity_provider: 'Google',
    state,
    code_challenge: challenge,
    code_challenge_method: 'S256',
  });
  window.location.assign(`https://${cognitoDomain}/oauth2/authorize?${params}`);
}

// Called on /auth/callback with the query string Cognito redirected back with.
export async function finishGoogleSignIn(search) {
  const params = new URLSearchParams(search);
  const failure = params.get('error_description') || params.get('error');
  if (failure) throw new Error(failure);

  const code = params.get('code');
  const verifier = sessionStorage.getItem(VERIFIER_KEY);
  if (!code || !verifier || params.get('state') !== sessionStorage.getItem(STATE_KEY))
    throw new Error('Вхід через Google не завершено. Спробуйте ще раз.');
  sessionStorage.removeItem(VERIFIER_KEY);
  sessionStorage.removeItem(STATE_KEY);

  const { cognitoDomain, userPoolClientId } = getConfig();
  const res = await fetch(`https://${cognitoDomain}/oauth2/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'authorization_code',
      client_id: userPoolClientId,
      code,
      redirect_uri: redirectUri(),
      code_verifier: verifier,
    }),
  });
  const tokens = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(tokens.error_description || tokens.error || 'Не вдалося увійти.');

  const idToken = new CognitoIdToken({ IdToken: tokens.id_token });
  const session = new CognitoUserSession({
    IdToken: idToken,
    AccessToken: new CognitoAccessToken({ AccessToken: tokens.access_token }),
    RefreshToken: new CognitoRefreshToken({ RefreshToken: tokens.refresh_token }),
  });
  // Saves the tokens in localStorage under this user, which makes it the "current user".
  new CognitoUser({ Username: idToken.payload['cognito:username'], Pool: userPool() })
    .setSignInUserSession(session);
}

export function signOut() {
  userPool().getCurrentUser()?.signOut();
}

// Deletes the signed-in user's Cognito account (after the API has deleted their data).
export function deleteCurrentUser() {
  return new Promise((resolve, reject) => {
    const user = userPool().getCurrentUser();
    if (!user) return resolve();
    user.getSession((err) => {
      if (err) return reject(err);
      user.deleteUser((e) => (e ? reject(e) : resolve()));
    });
  });
}

// Returns a valid session (refreshing tokens if needed) or null.
export function getSession() {
  return new Promise((resolve) => {
    const user = userPool().getCurrentUser();
    if (!user) return resolve(null);
    user.getSession((err, session) => resolve(err || !session?.isValid() ? null : session));
  });
}

// The API authorizer expects the ID token (it carries the email claim).
export async function getIdToken() {
  const session = await getSession();
  return session ? session.getIdToken().getJwtToken() : null;
}
