// Thin promise wrapper around amazon-cognito-identity-js (sign up / confirm / sign in / sign out).
import {
  AuthenticationDetails,
  CognitoUser,
  CognitoUserAttribute,
  CognitoUserPool,
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
    userPool().signUp(email, password, attrs, null, (err, res) => (err ? reject(err) : resolve(res)));
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

export function signIn(email, password) {
  return new Promise((resolve, reject) => {
    const details = new AuthenticationDetails({ Username: email, Password: password });
    cognitoUser(email).authenticateUser(details, {
      onSuccess: resolve,
      onFailure: reject,
    });
  });
}

export function signOut() {
  userPool().getCurrentUser()?.signOut();
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
