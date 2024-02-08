const Observation = require("./base.js").Observation;

class onSave extends Observation {
    constructor(bot) {
        super(bot);
        this.name = "onSave";
        this.obs = null;
        bot.on("save", (eventName) => {
            // Save entity status to local variable
            this.obs = eventName;
            this.bot.event(this.name);
        });
    }

    observe() {
        const result = this.obs;
        this.obs = null;
        return result;
    }
}

module.exports = onSave;
