import { ref, onValue } from "firebase/database";

export const mountStopsListener = (db, stopId, callback, cancel) => {
    if(stopId.length > 0) {
        const progressRef = ref(db, `stops/${stopId}`, cancel);
        const listener = onValue(progressRef, (snapshot) => {
            const data = snapshot.val()
            callback(data)
        })
        return listener
    } else return () => {}
}
