class Observation {
    constructor(bot) {
        if (new.target === Observation) {
            throw new TypeError(
                "Cannot instantiate abstract class Observation"
            );
        }

        this.bot = bot;
        this.name = "Observation";
    }

    observe() {
        throw new TypeError("Method 'observe()' must be implemented.");
    }

    reset() {}
}

function inject(bot, obs_list) {
    bot.obsList = [];
    bot.cumulativeObs = [];
    bot.eventMemory = {};
    obs_list.forEach((obs) => {
        bot.obsList.push(new obs(bot));
    });
    bot.event = function (event_name) {
        let result = {};
        bot.obsList.forEach((obs) => {
            if (obs.name.startsWith("on") && obs.name !== event_name) {
                return;
            }
            result[obs.name] = obs.observe();
        });
        bot.cumulativeObs.push([event_name, result]);
    };
    bot.observe = function () {
        bot.event("observe");
        const result = bot.cumulativeObs;
        bot.cumulativeObs = [];
        return JSON.stringify(result);
    };
}

module.exports = { Observation, inject };
