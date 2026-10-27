const count = document.querySelector('#count');
const add = document.querySelector('#add');
let clicks = 0;

add.addEventListener('click', () => {
  clicks += 1;
  count.textContent = String(clicks);
});
