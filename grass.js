const promptUser = require('inquirer').default;
const fileSystem = require('fs');
const WebSocketClient = require('ws');
const request = require('axios');
const moment = require('moment-timezone');
const { v4: generateUUID } = require('uuid');
require('colors');

console.error = function () {};

(async function initiate() {
  showHeader();
  await wait(1000);
  const configuration = new Configuration();
  const botInstance = new BotInstance(configuration);

  const userIDList = await loadLines('userid.txt');
  if (userIDList.length === 0) {
    console.error('Account is not available in userid.txt'.red);
    return;
  }
  console.log(`Detected total ${userIDList.length.toString().green} accounts, trying to connect...\n`.white);

  // Only connect directly without proxy
  const connectionTasks = userIDList.map(userID => botInstance.directConnect(userID));
  await Promise.all(connectionTasks);
})().catch(console.error);

function center(text) {
  const width = process.stdout.columns || 80;
  return text.padStart((width + text.length) / 2);
}

function showIntro() {
  console.log('\n');
  console.log(center("🌱 Grass Network 🌱").green.bold);
  console.log(center("GitHub: Caulia Wilson").cyan);
  console.log(center("Link: https://github.com/wcaulia").cyan);
}

function showHeader() {
  showIntro();
  console.log('\n');
  console.log(center("Processing, please wait a moment...").cyan.bold);
  console.log('\n');
}

class BotInstance {
  constructor(configuration) {
    this.configuration = configuration;
    this.totalDataUsage = {};
  }

  // Fungsi untuk koneksi langsung tanpa proxy
  async directConnect(userID) {
    try {
      const wsURL = `wss://${this.configuration.websocketHost}`;
      const wsClient = new WebSocketClient(wsURL, {
        headers: this.defaultHeaders(),
      });

      wsClient.on('open', () => {
        console.log(`Connect directly Without Proxy/Local network`.white);
        this.sendPing(wsClient, 'Direct IP'); // Memulai ping dengan update waktu real-time
      });

      wsClient.on('message', (msg) => {
        const message = JSON.parse(msg);
        const dataUsage = msg.length;
        if (!this.totalDataUsage[userID]) {
          this.totalDataUsage[userID] = 0;
        }
        this.totalDataUsage[userID] += dataUsage;

        if (message.action === 'AUTH') {
          const authResponse = {
            id: message.id,
            origin_action: 'AUTH',
            result: {
              browser_id: generateUUID(),
              user_id: userID,
              user_agent: 'Mozilla/5.0',
              timestamp: Math.floor(Date.now() / 1000),
              device_type: 'desktop',
              version: '4.28.2',
            },
          };
          wsClient.send(JSON.stringify(authResponse));
          console.log(`Trying to send authentication for userID: ${authResponse.result.user_id.yellow}`.white);
        } else if (message.action === 'PONG') {
          const totalDataUsageKB = (this.totalDataUsage[userID] / 1024).toFixed(2);
          const timezone = moment().tz('Asia/Jakarta').format('HH:mm:ss [WIB] DD-MM-YYYY');
          console.log(`${timezone} Received PONG for UserID: ${userID.green}, Used ${totalDataUsageKB.yellow} KB total packet data`.cyan);
        }
      });

      wsClient.on('close', (code, reason) => {
        console.log(`WebSocket closed, error ${code} ${reason}`.red);
        setTimeout(() => this.directConnect(userID), this.configuration.retryInterval);
      });

      wsClient.on('error', (error) => {
        console.error(`Error connecting to WebSocket`.red);
        wsClient.terminate();
      });
    } catch (error) {
      console.error(`Failed to connect directly: ${error.message}`.red);
    }
  }

  // Fungsi untuk mengirim ping dan memperbarui waktu setiap interval
  sendPing(wsClient, proxyIP) {
    setInterval(() => {
      const timezone = moment().tz('Asia/Jakarta').format('HH:mm:ss [WIB] DD-MM-YYYY');
      const pingMsg = {
        id: generateUUID(),
        version: '1.0.0',
        action: 'PING',
        data: {},
      };
      wsClient.send(JSON.stringify(pingMsg));
      console.log(`${timezone} Sent PING from ${proxyIP}`.green);
    }, 26000); // Kirim ping setiap 26 detik, sesuaikan jika perlu
  }

  defaultHeaders() {
    return {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0',
      Pragma: 'no-cache',
      'Accept-Language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7',
      'Cache-Control': 'no-cache',
      OS: 'Windows',
      Platform: 'Desktop',
      Browser: 'Mozilla',
    };
  }
}

class Configuration {
  constructor() {
    this.websocketHost = 'proxy.wynd.network:4444'; // You can change this to your desired WebSocket host
    this.retryInterval = 20000;  // Time to retry if connection fails
  }
}

async function loadLines(filePath) {
  return new Promise((resolve, reject) => {
    fileSystem.readFile(filePath, 'utf8', (err, data) => {
      if (err) {
        return reject(err);
      }
      resolve(data.split('\n').filter(line => line.trim() !== ''));
    });
  });
}

async function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}