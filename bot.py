import asyncio
import aiohttp

BASE = "https://sososisi.isonlab.net"

class Bot:
    def __init__(self, name, visibile):
        self.name = name
        self.visibile = visibile
        self.code = None
        self.ping_seconds = None

    async def auth(self, session):
        # Chiama /api/auth e salva il codice e l'intervallo di ping
        async with session.get(BASE + f"/api/auth?name={self.name}") as r:
            data = await r.json()
        print(data)
        self.code = data["code"]
        self.ping_seconds = data["pingEverySeconds"]

    async def ping(self, session):
        # Manda il ping con la visibilità attuale
        vis = "visible" if self.visibile else "invisible"
        async with session.get(BASE + f"/api/ping?code={self.code}&visible={vis}") as r:
            data = await r.json()
        print("Ping:", data)
        # Ritorna True se ok, False se il codice è stato distrutto
        return data["ok"]

    async def get_players(self, session):
        # Ritorna la lista dei giocatori nel round
        async with session.get(BASE + f"/api/players?code={self.code}") as r:
            data = await r.json()
        print("Giocatori:", data)
        return data if isinstance(data, list) else data.get("players", [])

    async def fire(self, session, target):
        # Spara a un giocatore
        async with session.get(BASE + f"/api/fire?code={self.code}&target={target}") as r:
            print("Fuoco:", await r.json())

    async def leggi_comandi(self):
        loop = asyncio.get_event_loop()
        while True:
            # run_in_executor serve perché input() è bloccante,
            # così non blocca il resto del programma mentre aspetta
            cmd = await loop.run_in_executor(None, input)
            if cmd == "v":
                self.visibile = not self.visibile
                print(f"Visibilità cambiata: {self.visibile}")

    async def ping_loop(self, session):
        while True:
            # Aspetta il numero di secondi giusto prima di pingare
            await asyncio.sleep(self.ping_seconds)

            ok = await self.ping(session)
            if not ok:
                print("Codice distrutto! Riavvia il bot.")
                break

            # Se sono invisibile salto la parte del fuoco
            if not self.visibile:
                continue

            # Spara a tutti i giocatori visibili (tranne me stesso)
            players = await self.get_players(session)
            for player in players:
                if player["name"] != self.name and player["visible"]:
                    await self.fire(session, player["name"])

    async def run(self):
        # Apre una sessione HTTP riusabile per tutte le chiamate
        async with aiohttp.ClientSession() as session:
            await self.auth(session)
            print(f"Codice: {self.code}")
            print(f"Visibile: {self.visibile}")
            print("Premi 'v' + invio per cambiare visibilità")

            # Fa girare ping_loop e leggi_comandi in parallelo
            await asyncio.gather(
                self.ping_loop(session),
                self.leggi_comandi()
            )


# --- AVVIO ---
name = "Ebola"
scelta = input("Vuoi essere visibile? (s/n): ")
visibile = scelta == "s"

bot = Bot(name, visibile)
asyncio.run(bot.run())