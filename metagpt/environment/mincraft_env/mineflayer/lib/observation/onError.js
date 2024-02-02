const Observation = require("./base.js").Observation;

class onError extends Observation {
    constructor(bot) {
        super(bot);
        this.name = "onError";
        this.obs = null;
        bot.on("error", (err) => {
            // Save entity status to local variable
            this.obs = err;
            this.bot.event(this.name);
        });
    }

    observe() {
        const result = this.obs;
        this.obs = null;
        return result;
    }
}

module.exports = onError;
