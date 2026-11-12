// A quiet console is not enough: the bot must reach the game's result screen.
function assertRunComplete({ completed, over, score, errs, guard, lastState }) {
  const reasons = [];
  if (!completed) reasons.push('Bot sefer sonuna ulaşamadı (adım sınırı: ' + guard + '). Son durum: ' + JSON.stringify(lastState));
  if (!over || !Number.isFinite(score)) reasons.push('Tamamlanmış sefer ve geçerli sonuç bulunamadı.');
  if (errs.length) reasons.push('Sayfa hataları: ' + errs.join(' | '));
  if (reasons.length) throw new Error(reasons.join('\n'));
}
module.exports = { assertRunComplete };
