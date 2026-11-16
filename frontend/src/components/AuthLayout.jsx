import { Shelf } from './Bookshelf.jsx';

// Login / register layout: the form on a cream card, a wine panel with a small wall shelf beside it.
const SHELF = [
  { title: 'Тіні забутих предків', author: 'Михайло Коцюбинський' },
  { title: 'Місто', author: 'Валер’ян Підмогильний' },
  { title: 'Jane Eyre', author: 'Charlotte Brontë' },
  { title: 'Лісова пісня', author: 'Леся Українка' },
  { title: 'Intermezzo', author: 'Михайло Коцюбинський' },
  { title: 'Frankenstein', author: 'Mary Shelley' },
  { title: 'Сад Гетсиманський', author: 'Іван Багряний' },
  { title: 'Маруся Чурай', author: 'Ліна Костенко' },
];

export default function AuthLayout({ children }) {
  return (
    <div className="auth">
      {children}
      <aside className="auth__aside">
        <p className="auth__quote">
          Книга, яку ти вже прочитав, ще не прочитав хтось інший.
          <small>ReadCycle · обмін книгами в УКУ</small>
        </p>
        <Shelf variant="wall" books={SHELF} />
      </aside>
    </div>
  );
}
