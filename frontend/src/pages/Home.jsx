import { Cabinet, Shelf, chunk } from '../components/Bookshelf.jsx';

// Main page. For now the oak cabinet shows sample books; on stage 5 it will be filled from the
// API (all books of other students) and get the filter panel.
const SAMPLE = [
  ['Кобзар', 'Тарас Шевченко'],
  ['Тіні забутих предків', 'Михайло Коцюбинський'],
  ['Місто', 'Валер’ян Підмогильний'],
  ['Хіба ревуть воли', 'Панас Мирний'],
  ['Лісова пісня', 'Леся Українка'],
  ['Захар Беркут', 'Іван Франко'],
  ['Маруся Чурай', 'Ліна Костенко'],
  ['Сад Гетсиманський', 'Іван Багряний'],
  ['Солодка Даруся', 'Марія Матіос'],
  ['Felix Austria', 'Софія Андрухович'],
  ['Музей покинутих секретів', 'Оксана Забужко'],
  ['Ворошиловград', 'Сергій Жадан'],
  ['Jane Eyre', 'Charlotte Brontë'],
  ['Pride and Prejudice', 'Jane Austen'],
  ['Frankenstein', 'Mary Shelley'],
  ['The Picture of Dorian Gray', 'Oscar Wilde'],
  ['Les Misérables', 'Victor Hugo'],
  ['Anna Karenina', 'Leo Tolstoy'],
  ['Moby-Dick', 'Herman Melville'],
  ['Wuthering Heights', 'Emily Brontë'],
  ['The Great Gatsby', 'F. Scott Fitzgerald'],
  ['Intermezzo', 'Михайло Коцюбинський'],
  ['Записки українського самашедшого', 'Ліна Костенко'],
  ['Інтернат', 'Сергій Жадан'],
  ['Little Women', 'Louisa May Alcott'],
  ['Dracula', 'Bram Stoker'],
  ['Rebecca', 'Daphne du Maurier'],
  ['Persuasion', 'Jane Austen'],
  ['Emma', 'Jane Austen'],
  ['Middlemarch', 'George Eliot'],
  ['Лебедина зграя', 'Василь Земляк'],
  ['Земля', 'Ольга Кобилянська'],
].map(([title, author]) => ({ title, author }));

export default function Home() {
  return (
    <section>
      <div className="hero">
        <div className="card">
          <span className="eyebrow">Обмін книгами між студентами УКУ</span>
          <h1>
            Віддай прочитане — <span className="serif-italic">знайди своє</span>
          </h1>
          <p className="muted">
            Склади полицю з книжок, які готова віддати чи обміняти, додай вішліст — і ReadCycle
            підкаже, з ким вам варто помінятися.
          </p>
        </div>
        <div className="card card--wine">
          <span className="eyebrow" style={{ color: 'var(--gold-soft)' }}>
            Скоро
          </span>
          <h2>Твоя полиця</h2>
          <p>Профіль, власна бібліотека, вішліст і пошук обміну з’являться на наступних етапах.</p>
        </div>
      </div>

      <span className="preview-ribbon">
        Попередній перегляд: тут з’являться книги інших студентів
      </span>
      <Cabinet title="ReadCycle">
        {chunk(SAMPLE, 17).map((row, i) => (
          <Shelf key={i} books={row} />
        ))}
      </Cabinet>
    </section>
  );
}
