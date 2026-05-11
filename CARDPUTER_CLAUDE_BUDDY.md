# Claude Buddy — M5Stack Cardputer Integration

Run the Ascended Intelligence Core (AICI) as a pocket AI assistant on the M5Stack Cardputer.

---

## What This Is

The Cardputer Claude Buddy turns your M5Stack Cardputer into a handheld terminal that talks to the AICI backend over Wi-Fi. Type a query on the Cardputer keyboard, send it to the `/execute` endpoint, and read the AI response on the built-in display.

```
[Cardputer keyboard] → HTTP POST /execute → [AICI API] → [response on display]
```

---

## Hardware Requirements

| Item | Notes |
|------|-------|
| M5Stack Cardputer | ESP32-S3 + 1.14" LCD + full keyboard |
| Wi-Fi network | 2.4 GHz, WPA2 |
| Host machine | Runs the AICI Flask/Gunicorn server |

---

## Backend Setup (Host Machine)

### 1. Clone & install

```bash
git clone https://github.com/jjlogic2011-maker/ascended-intelligence-core.git
cd ascended-intelligence-core
pip install -r requirements.txt
```

### 2. Set environment variables

```bash
export AICI_API_KEY=your-secret-key-here
```

Or create a `.env` file:

```
AICI_API_KEY=your-secret-key-here
```

### 3. Run the server

**Development:**
```bash
flask --app api/app.py run --host=0.0.0.0 --port=5000
```

**Production:**
```bash
gunicorn -w 2 -b 0.0.0.0:5000 "api.app:app"
```

### 4. Verify the server is up

```bash
curl http://localhost:5000/health
# {"status": "healthy"}
```

Make note of your host machine's local IP address (e.g. `192.168.1.42`). The Cardputer firmware needs it.

---

## Cardputer Firmware

### Prerequisites

- [Arduino IDE](https://www.arduino.cc/en/software) ≥ 2.x  
- [M5Stack board package](https://docs.m5stack.com/en/arduino/arduino_ide) installed  
- Libraries: `M5Cardputer`, `ArduinoJson`, `HTTPClient` (all via Library Manager)

### Sketch

Create a new sketch named `claude_buddy.ino` and paste the code below. Fill in your Wi-Fi credentials, server IP, and API key.

```cpp
#include <M5Cardputer.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ── Configuration ──────────────────────────────────────────────
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* SERVER_IP     = "192.168.1.42";   // host machine IP
const int   SERVER_PORT   = 5000;
const char* API_KEY       = "your-secret-key-here";
// ───────────────────────────────────────────────────────────────

String inputBuffer = "";

void setup() {
    auto cfg = M5.config();
    M5Cardputer.begin(cfg);
    M5Cardputer.Display.setRotation(1);
    M5Cardputer.Display.setTextSize(1);
    M5Cardputer.Display.fillScreen(BLACK);
    M5Cardputer.Display.setTextColor(GREEN);
    M5Cardputer.Display.println("Claude Buddy v1.0");
    M5Cardputer.Display.println("Connecting to Wi-Fi...");

    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        M5Cardputer.Display.print(".");
    }
    M5Cardputer.Display.println("\nReady. Type & press Enter.");
}

void sendQuery(const String& query) {
    if (WiFi.status() != WL_CONNECTED) {
        M5Cardputer.Display.println("[ERR] Wi-Fi lost");
        return;
    }

    HTTPClient http;
    String url = "http://" + String(SERVER_IP) + ":" + SERVER_PORT + "/execute";
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("x-api-key", API_KEY);

    StaticJsonDocument<256> doc;
    doc["type"]  = "report";
    doc["query"] = query;
    String body;
    serializeJson(doc, body);

    int code = http.POST(body);
    M5Cardputer.Display.fillScreen(BLACK);
    M5Cardputer.Display.setCursor(0, 0);

    if (code == 200) {
        String payload = http.getString();
        StaticJsonDocument<512> resp;
        deserializeJson(resp, payload);
        const char* result = resp["result"] | "no result";
        M5Cardputer.Display.setTextColor(CYAN);
        M5Cardputer.Display.println(result);
    } else {
        M5Cardputer.Display.setTextColor(RED);
        M5Cardputer.Display.printf("[HTTP %d]\n", code);
    }

    http.end();
    M5Cardputer.Display.setTextColor(WHITE);
    M5Cardputer.Display.println("\n> ");
}

void loop() {
    M5Cardputer.update();

    if (M5Cardputer.Keyboard.isChange() && M5Cardputer.Keyboard.isPressed()) {
        Keyboard_Class::KeysState state = M5Cardputer.Keyboard.keysState();

        for (char c : state.word) {
            if (c == '\n' || c == '\r') {
                if (inputBuffer.length() > 0) {
                    M5Cardputer.Display.println();
                    sendQuery(inputBuffer);
                    inputBuffer = "";
                }
            } else if (c == '\b' && inputBuffer.length() > 0) {
                inputBuffer.remove(inputBuffer.length() - 1);
                M5Cardputer.Display.print('\b');
            } else {
                inputBuffer += c;
                M5Cardputer.Display.print(c);
            }
        }
    }
}
```

### Flash

1. Connect the Cardputer via USB-C.
2. Select **Tools → Board → M5Stack → M5Cardputer**.
3. Select the correct COM port.
4. Click **Upload**.

---

## Task Types

The AICI router (`agents/router.py`) supports two task types you can set in the sketch:

| `type` value | Handler | What it does |
|---|---|---|
| `"report"` | `experts/report.py` | Generates a structured report |
| `"security"` | `experts/security.py` | Runs a security check |
| `"buddy"` | `experts/buddy.py` | Conversational assistant reply |

Change `doc["type"] = "report"` in the sketch to switch modes.

---

## API Reference

### `POST /execute`

**Headers**

```
Content-Type: application/json
x-api-key: <AICI_API_KEY>
```

**Request body**

```json
{
  "type": "report",
  "query": "What is the status of the system?"
}
```

**Response**

```json
{
  "status": "executed",
  "result": "<response text>"
}
```

**Error responses**

| Code | Meaning |
|------|---------|
| 401 | Missing or wrong `x-api-key` |
| 400 | Malformed JSON body |

---

## Running the Test Suite

```bash
pip install -r requirements-dev.txt
pytest
```

All unit and integration tests live under `tests/`.

---

## Docker Deployment

```bash
docker build -t aici-core .
docker run -e AICI_API_KEY=your-secret-key-here -p 5000:5000 aici-core
```

The Cardputer connects to the Docker host IP on port 5000 — no other changes needed in the firmware.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `[HTTP 401]` on display | API key mismatch — check `AICI_API_KEY` env var and sketch constant |
| `[ERR] Wi-Fi lost` | Move Cardputer closer to AP; check SSID/password |
| Display shows nothing after boot | Re-flash; hold power button for 6 s to hard-reset |
| `curl /health` fails | Server not bound to `0.0.0.0` — add `--host=0.0.0.0` to Flask run |
| Upload fails in Arduino IDE | Wrong COM port or board selection; try a different USB cable |

---

## Security Notes

- The default `AICI_API_KEY` in `security/auth.py` is `"change-me"` — always override it via the environment variable before exposing the server on any network.
- Do not hard-code the real API key in source control; use the `.env` file (which is in `.gitignore`) or a secrets manager.
- For production use, put the server behind TLS (nginx + Let's Encrypt) and update the Cardputer sketch to use `https://` with `WiFiClientSecure`.

---

## Project Structure

```
ascended-intelligence-core/
├── api/
│   ├── app.py              # Flask app, /execute endpoint
│   └── infrastructure/
│       └── config.py
├── agents/
│   └── router.py           # Routes tasks to expert handlers
├── experts/
│   ├── report.py           # Report generation expert
│   └── security.py         # Security check expert
├── core/
│   └── orchestrator.py     # Runs route_task, wraps result
├── security/
│   └── auth.py             # x-api-key verification
├── tests/
├── requirements.txt
├── Dockerfile
└── CARDPUTER_CLAUDE_BUDDY.md  ← this file
```
