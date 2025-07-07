import http from 'k6/http';
import { sleep, check } from 'k6';
import { Counter, Rate } from 'k6/metrics';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Métricas personalizadas
const successfulVotes = new Counter('successful_votes');
const failedVotes = new Counter('failed_votes');
const voteRate = new Rate('vote_rate');

// Configuración de escenarios de carga
export let options = {
    scenarios: {
        constant_load: {
            executor: 'constant-vus',
            vus: 50,
            duration: '20s',
        },
        ramp_up: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '10s', target: 100 },
                { duration: '30s', target: 100 },
                { duration: '10s', target: 0 },
            ],
            gracefulRampDown: '5s',
        },
    },
    thresholds: {
        http_req_duration: ['p(95)<500'], // 95% de las peticiones deben completarse en menos de 500ms
        'vote_rate': ['rate>0.9'],        // Al menos 90% de los votos deben ser exitosos
    },
};

// Lista de encuestas disponibles para votar
const availablePolls = [1, 2, 3, 4, 5];

// Función principal
export default function () {
    // Seleccionar una encuesta aleatoria
    const pollId = availablePolls[randomIntBetween(0, availablePolls.length - 1)];
    
    // Seleccionar una opción aleatoria (suponiendo máximo 5 opciones)
    const choice = randomIntBetween(0, 4);
    
    // Realizar la votación
    vote(pollId, choice);
    
    // Tiempo de espera entre peticiones
    sleep(randomIntBetween(1, 5) / 10);
}

// Función para votar en una encuesta
function vote(pollId, choice) {
    const url = `http://localhost/polls/${pollId}/vote`;
    const payload = JSON.stringify({ choice: choice });
    const params = {
        headers: { 'Content-Type': 'application/json' },
    };

    const response = http.post(url, payload, params);
    
    // Verificar la respuesta
    const success = check(response, {
        'status is 200': (r) => r.status === 200,
        'response body contains success': (r) => r.body.includes('success'),
    });
    
    // Registrar métricas
    if (success) {
        successfulVotes.add(1);
        voteRate.add(1);
    } else {
        failedVotes.add(1);
        voteRate.add(0);
        console.log(`Error al votar en encuesta ${pollId}, opción ${choice}: ${response.status} - ${response.body}`);
    }
}

// Función para obtener todas las encuestas (simulada)
function getPolls() {
    const response = http.get('http://localhost/polls');
    if (response.status === 200) {
        return JSON.parse(response.body);
    }
    return [];
}