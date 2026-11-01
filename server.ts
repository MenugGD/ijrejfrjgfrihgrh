import express, { Request, Response } from 'express';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { INITIAL_PROJECT } from './src/initialData';
import { TournamentProject } from './src/types';
import { rivalOf } from './src/utils/bracketLogic';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3000;

app.use(express.json({ limit: '35mb' }));

// Database directory & persistent file
const DATA_DIR = path.join(__dirname, 'data');
const DB_FILE = path.join(DATA_DIR, 'tournament_maker_db.json');

if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

let projectState: TournamentProject = JSON.parse(JSON.stringify(INITIAL_PROJECT));

// Active versus match view (for OBS broadcast sync)
let activeVersus: {
  isOpen: boolean;
  tab: number;
  matchIdx: number;
  lastAction?: {
    type: 'pick_winner' | 'cinematic' | 'advance';
    winnerSide?: 0 | 1;
    winnerName?: string;
    timestamp: number;
  };
} = {
  isOpen: false,
  tab: 0,
  matchIdx: 0,
};

// Load database if exists
if (fs.existsSync(DB_FILE)) {
  try {
    const raw = fs.readFileSync(DB_FILE, 'utf-8');
    const parsed = JSON.parse(raw);
    if (parsed && parsed.slots && typeof parsed.slots === 'object') {
      projectState = {
        ...INITIAL_PROJECT,
        ...parsed,
      };
    }
  } catch (err) {
    console.error('Error loading tournament DB:', err);
  }
} else {
  try {
    fs.writeFileSync(DB_FILE, JSON.stringify(projectState, null, 2), 'utf-8');
  } catch (err) {
    console.error('Error creating tournament DB:', err);
  }
}

function saveDatabase() {
  try {
    fs.writeFileSync(DB_FILE, JSON.stringify(projectState, null, 2), 'utf-8');
  } catch (err) {
    console.error('Failed to save tournament DB:', err);
  }
}

// SSE Clients
type SSEClient = {
  id: number;
  res: Response;
};
let clients: SSEClient[] = [];
let clientIdCounter = 0;

function broadcast(eventType = 'state_update') {
  projectState.lastUpdated = Date.now();
  saveDatabase();

  const payload = JSON.stringify({
    project: projectState,
    versus: activeVersus,
    timestamp: Date.now(),
  });

  clients.forEach(c => {
    try {
      c.res.write(`event: ${eventType}\ndata: ${payload}\n\n`);
    } catch {
      // client write error
    }
  });
}

// SSE Endpoint
app.get('/api/stream', (req: Request, res: Response) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache, no-transform');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('Access-Control-Allow-Origin', '*');

  const clientId = ++clientIdCounter;
  const newClient: SSEClient = { id: clientId, res };
  clients.push(newClient);

  res.write(`event: connected\ndata: ${JSON.stringify({ project: projectState, versus: activeVersus })}\n\n`);

  req.on('close', () => {
    clients = clients.filter(c => c.id !== clientId);
  });
});

// REST Endpoints
app.get('/api/project', (_req: Request, res: Response) => {
  res.json({ project: projectState, versus: activeVersus });
});

// Save / update project settings
app.post('/api/project/update', (req: Request, res: Response) => {
  const { title, background, chroma, transparent, slots, eliminated } = req.body;

  if (title !== undefined) projectState.title = String(title);
  if (background !== undefined) projectState.background = { ...projectState.background, ...background };
  if (chroma !== undefined) projectState.chroma = chroma;
  if (transparent !== undefined) projectState.transparent = Boolean(transparent);
  if (slots !== undefined) projectState.slots = { ...projectState.slots, ...slots };
  if (eliminated !== undefined) projectState.eliminated = eliminated;

  broadcast('state_update');
  res.json({ success: true, project: projectState });
});

// Advance winner from srcKey to dstKey (Tournament Maker logic)
app.post('/api/project/advance', (req: Request, res: Response) => {
  const { srcKey, dstKey, winnerSide, winnerName } = req.body;
  if (!srcKey || !dstKey || !projectState.slots[srcKey]) {
    res.status(400).json({ error: 'Invalid srcKey or dstKey' });
    return;
  }

  // Copy participant to destination
  projectState.slots[dstKey] = { ...projectState.slots[srcKey]! };

  // Remove eliminated status from src and dst
  projectState.eliminated = projectState.eliminated.filter(k => k !== srcKey && k !== dstKey);

  // Mark rival as eliminated
  const rival = rivalOf(srcKey);
  if (rival && projectState.slots[rival]) {
    if (!projectState.eliminated.includes(rival)) {
      projectState.eliminated.push(rival);
    }
  }

  activeVersus.lastAction = {
    type: dstKey === 'C:0:0' ? 'cinematic' : 'pick_winner',
    winnerSide,
    winnerName: winnerName || projectState.slots[srcKey]?.name,
    timestamp: Date.now(),
  };

  broadcast('winner_advanced');
  res.json({ success: true, project: projectState, versus: activeVersus });
});

// Swap or set slot participant
app.post('/api/project/slot', (req: Request, res: Response) => {
  const { key, participant } = req.body;
  if (!key) {
    res.status(400).json({ error: 'Missing key' });
    return;
  }

  projectState.slots[key] = participant;
  broadcast('slot_updated');
  res.json({ success: true, project: projectState });
});

// Toggle eliminated marker
app.post('/api/project/toggle-eliminated', (req: Request, res: Response) => {
  const { key } = req.body;
  if (!key) {
    res.status(400).json({ error: 'Missing key' });
    return;
  }

  if (projectState.eliminated.includes(key)) {
    projectState.eliminated = projectState.eliminated.filter(k => k !== key);
  } else if (projectState.slots[key]) {
    projectState.eliminated.push(key);
  }

  broadcast('state_update');
  res.json({ success: true, eliminated: projectState.eliminated });
});

// Versus overlay live navigation sync
app.post('/api/versus/sync', (req: Request, res: Response) => {
  const { isOpen, tab, matchIdx, action } = req.body;
  if (isOpen !== undefined) activeVersus.isOpen = Boolean(isOpen);
  if (tab !== undefined) activeVersus.tab = Number(tab);
  if (matchIdx !== undefined) activeVersus.matchIdx = Number(matchIdx);
  if (action) activeVersus.lastAction = { ...action, timestamp: Date.now() };

  broadcast('versus_sync');
  res.json({ success: true, versus: activeVersus });
});

// Reset tournament
app.post('/api/project/reset', (req: Request, res: Response) => {
  projectState = JSON.parse(JSON.stringify(INITIAL_PROJECT));
  activeVersus = { isOpen: false, tab: 0, matchIdx: 0 };
  broadcast('tournament_reset');
  res.json({ success: true, project: projectState });
});

async function startServer() {
  const isProduction = process.env.NODE_ENV === 'production';

  if (!isProduction) {
    const { createServer: createViteServer } = await import('vite');
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static(path.join(__dirname, 'dist')));
    app.get('*', (_req: Request, res: Response) => {
      res.sendFile(path.join(__dirname, 'dist', 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Tournament Maker Server running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
