function getRandomNumberInRange(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

function getRandomFromList(list) {
    const randomIndex = Math.floor(Math.random() * list.length);
    return list[randomIndex];
  }
module.exports = { getRandomNumberInRange, getRandomFromList };
