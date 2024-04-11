let gameTimeCounter = 0;
let gameTimeList = [];
const initCounter = (bot) => {
    gameTimeList = [];
    for (let i = 0; i < 13000; i += 1000) {
        gameTimeList.push(i);
    }
    for (let i = 13000; i < 24000; i += 2000) {
        gameTimeList.push(i);
    }
    const timeOfDay = bot.time.timeOfDay;
    for (let i = 0; i < gameTimeList.length; i++) {
        if (gameTimeList[i] > timeOfDay) {
            gameTimeCounter = i - 1;
            break;
        }
    }
};

const getNextTime = () => {
    gameTimeCounter++;
    if (gameTimeCounter >= gameTimeList.length) {
        gameTimeCounter = 0;
    }
    return gameTimeList[gameTimeCounter];
};

module.exports = {
    initCounter,
    getNextTime,
};
