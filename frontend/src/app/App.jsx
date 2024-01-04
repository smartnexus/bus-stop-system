import React, {useState, useRef, useEffect} from "react"

import '../styles/App.css';

import { initializeApp } from "firebase/app";
import { getDatabase } from "firebase/database";
import { firebaseConfig } from '../config/firebase';

import { mountStopsListener } from "../actions/listen"
import { colors } from "../config/colors";

const app = initializeApp(firebaseConfig);
const db = getDatabase(app);

function App() {
    const [stopId, setStopId] = useState('');
    const [online, setOnline] = useState(false)
    const [data, setData] = useState()
    let obs = useRef(() => {})

    useEffect(() => {
        obs.current()
        setOnline(false)
        obs.current = mountStopsListener(db, stopId, content => {
            if(content) {
                setOnline(true)
                setData({
                    list: Object.keys(content), content
                })
            } else {
                setData({
                    list: [], content: undefined
                })
            }
        }, () => setOnline(false));

        return () => {
            obs.current()
            setOnline(false)
        }
    }, [stopId, setData, setOnline])

    return (
        <div className="App">
        <header className="App-header">
            <div className="Main-box">
                <input className="w3-input w3-border w3-round-large" type="number" value={stopId} placeholder="Escribe la parada..." onChange={(e) => setStopId(e.target.value)}/>
                <div className="Results-box">
                    {online && stopId !== '' ?
                        data.list.map(o => (
                            <BusBox line={o.split('-')[0]} number={o.split('-')[1]} dis={data.content[o]?.last?.dis} est={data.content[o]?.est}/>
                        )):<p>La parada seleccionada no existe.</p>
                    }
                </div>
            </div>
            <p className="bottom">Made with React 18 <img alt="logo" style={{verticalAlign: 'middle'}} width={'22px'} src="/favicon.ico"/></p>
        </header>
        </div>
    );
}

const BusBox = ({ line, number, dis, est}) => (
    <div className="Bus-box">
        <div className="line" style={{backgroundColor: colors[line]}}>
            <h3><b>{line}</b></h3>
        </div>
        <div className="info">
            <h5><b>Coche número {number} de la ruta</b></h5>
            <h5>{est}min ({Math.round(dis)}m)</h5>
        </div>
    </div>
)

export default App;
