import { https } from "firebase-functions";
import admin from "firebase-admin";
import { calculateToken } from "../FirebaseTD/functions/solve.js";
import { Solver } from "../FirebaseTD/functions/ws.js";

admin.initializeApp();
const db = admin.firestore();

/**
 * Middleware: Authenticate requests using Bearer token (UID)
 */
const authenticateUser = async (req) => {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
        throw new https.HttpsError("unauthenticated", "Not Authorized");
    }

    const uid = authHeader.split("Bearer ")[1];

    try {
        await admin.auth().getUser(uid);
        return uid;
    } catch (error) {
        throw new https.HttpsError("unauthenticated", "Invalid UID");
    }
};

/**
 * Function to increment request count for a UID in Firestore (Runs in background)
 */
const incrementRequestCount = (uid) => {
    const userRef = db.collection("requestCounts").doc(uid);

    userRef.set(
        { count: admin.firestore.FieldValue.increment(1) },
        { merge: true }
    );
};

/**
 * POST /td - Handle TD requests
 */
export const td = https.onRequest(async (req, res) => {
    if (req.method !== "POST") {
        return res.status(405).send("Method Not Allowed");
    }

    try {
        const uid = await authenticateUser(req);
        incrementRequestCount(uid);

        const json = req.body;
        const { data, signer, ua } = await Solver(json.userAgent, json.ip, new Date().getTime());
        const signed = signer(json.endpoint, json.currentPath);

        res.json({ data, signed, ua });
    } catch (error) {
        console.error("Error in /td:", error);
        res.status(403).send(error.message || "Unauthorized");
    }
});

/**
 * POST /token - Handle Token requests
 */
export const token = https.onRequest(async (req, res) => {
    if (req.method !== "POST") {
        return res.status(405).send("Method Not Allowed");
    }

    try {
        const uid = await authenticateUser(req);
        incrementRequestCount(uid);

        const { result } = req.body;
        const token = calculateToken(result);

        if (token === "fail") {
            return res.status(400).send("Invalid token");
        }

        res.json({ token });
    } catch (error) {
        console.error("Error in /token:", error);
        res.status(403).send(error.message || "Unauthorized");
    }
});
