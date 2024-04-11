const Observation = require("./base.js").Observation;

class onChat extends Observation {
    constructor(bot) {
        super(bot);
        this.name = "onChat";
        this.obs = "";
        bot.on("chatEvent", (username, message) => {
            // Save entity status to local variable
            if (message.startsWith("/")) {
                return;
            }

            this.obs += message;
            this.bot.event(this.name);
        });
    }

    observe() {
        const result = this.obs;
        this.obs = "";
        return result;
    }
}

module.exports = onChat;
