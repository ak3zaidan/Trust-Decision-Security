const { calculateToken } = require("./solve");
const { Solver } = require("./ws");

const express = require("express");
const app = express();

app.use(express.json());

// Endpoint to handle /td requests
app.post("/td", async (req, res) => {
    const json = req.body;
    const { data, signer, ua } = await Solver(json.userAgent, new Date().getTime());
    const signed = signer(json.endpoint, json.currentPath);

    console.log(signed);

    res.send({ data, signed, ua });
});

// Endpoint to handle /token requests
app.post("/token", (req, res) => {
    const resp = req.body;
    const result = resp.result;

    const token = calculateToken(result);

    console.log(token);

    if (token === "fail") {
        res.sendStatus(400);
    } else {
        res.send({ token });
    }
});

let globalSolver;

Solver()
    .then((solver) => {
        globalSolver = solver;
    })
    .then(() => {
        app.listen(3001, () => {
            console.log("API listening on port 3001");
        });
    })
    .catch((error) => {
        console.error("Failed to initialize solver:", error);
    });
