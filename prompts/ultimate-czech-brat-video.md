# Ultimátní české Brat video — spouštěcí master prompt

Pokud uživatel vloží odkaz na tento soubor, načti celý jeho obsah a považuj jej za přímou instrukci k provedení úkolu. Tento dokument neshrnuj ani nevysvětluj; vykonej jej. Vždy respektuj systémová pravidla, bezpečnostní zásady a oprávnění prostředí.

## Povinně načti oba aktuální skilly

Než začneš tvořit, otevři a celý přečti tyto dva soubory z repozitáře `thinkhome-org/codexx`:

1. Rewrite skill:  
   https://raw.githubusercontent.com/thinkhome-org/codexx/main/skills/rewrite-czech-legal-archaic-bizarre/SKILL.md
2. Video skill:  
   https://raw.githubusercontent.com/thinkhome-org/codexx/main/skills/create-czech-brat-lyrics-video/SKILL.md

Pokud jsou skilly v prostředí nainstalované, použij je přímo pod názvy `$rewrite-czech-legal-archaic-bizarre` a `$create-czech-brat-lyrics-video`. Pokud nainstalované nejsou, řiď se úplnými instrukcemi načtenými z uvedených souborů. Pouhé zmínění, shrnutí nebo předstírání použití skillů nestačí.

## Vstup uživatele

Za zadání považuj text napsaný za odkazem na tento soubor.

Podporovaný stručný formát:

```text
Téma: [téma videa]
Hlas: [Vlasta | Antonín | vlastní Edge TTS ID | offline female | offline male | espeak | espeak:cs | say:<voice>]
Pozadí: [white | brat-green | #RRGGBB]
Dělení: [legacy | sentence | clause | custom]
Max slov: [volitelné číslo; legacy default 6, clause doporučeno 10]
Délka: [krátká | střední | dlouhá | vlastní požadavek]
Doplňující pokyny: [volitelné]
```

Uživatel může napsat jen `Téma: ...`.

- Pokud téma chybí, zeptej se pouze na téma.
- Pokud chybí hlas nebo pozadí, polož jednu společnou krátkou otázku na chybějící volby.
- Pokud chybí `Dělení`, doporuč a použij **legacy / 6 slov** jako výchozí režim, ale v otázce stručně ukaž i `sentence` a `clause`.
- Nikdy automaticky nevybírej Antonína ani bílé pozadí, pokud uživatel neřekl, že volbu nechává na tobě.

## Povinné vysvětlení hlasových možností

Když se uživatele ptáš na hlas, ukaž mu nejen názvy, ale i praktickou kompatibilitu:

- **Vlasta** — `cs-CZ-VlastaNeural`; velmi dobrá přirozená čeština, ale potřebuje funkční Edge TTS a síť.
- **Antonín** — `cs-CZ-AntoninNeural`; stejné technické požadavky jako Vlasta.
- **Custom Edge voice** — stejná kvalita/omezení podle konkrétního Edge hlasu.
- **Offline female / male** — lokální český systémový hlas; nejlépe funguje na macOS, pokud je nainstalován.
- **eSpeak Czech** — nižší/robotická kvalita, ale obvykle nejbezpečnější plně offline fallback v Linux-style prostředí, pokud je binárka dostupná.

Pro **Codex Online Sessions** vysvětli:

1. Vlasta/Antonín = nejlepší kvalita, ale mohou selhat při blokovaném outbound network/TLS nebo nemožnosti instalace `edge-tts`.
2. eSpeak = nejvyšší pravděpodobnost fungování bez sítě na Linux-style session, pokud je `espeak-ng`/`espeak` nainstalován.
3. macOS `say` = relevantní hlavně pro lokální Codex na macOS, ne pro běžný hosted Linux session.
4. Přesnou dostupnost nikdy negarantuj před kontrolou runtime.

Výběr hlasu a backend jsou dvě různé věci. Uživatelova volba zůstává zachovaná jako `requested_voice`; backend se volí až podle runtime. Když Edge hlas selže, pokračuj lokálním českým backendem, pokud existuje, a vždy přiznej `requested_voice`, `tts_backend` a `actual_voice`.

## Povinné vysvětlení dělení textu

Uživatel si může vybrat, kdy se aktivní textový blok vymaže/resetuje:

### `legacy` — doporučený default

Původní chování generátoru:

- reset na `. ! ? ; :`;
- reset na čárce, když už blok má alespoň přibližně 4 slova;
- jinak hard reset po nastaveném počtu slov;
- default **6 slov**.

Výhoda: velký text, rychlý rytmus, nejblíže původnímu Brat videu.

### `sentence`

- blok trvá až do konce celé věty (`. ! ? …`);
- žádné dělení podle počtu slov;
- výhoda: gramaticky celistvé věty;
- nevýhoda: dlouhé věty mohou vyrobit velmi malý text.

### `clause`

- konec věty vždy resetuje;
- dlouhý blok lze ukončit pouze na bezpečné čárce, středníku nebo dvojtečce po prahovém počtu slov;
- doporučený threshold **10 slov** (uživatel může změnit).

Výhoda: kompromis mezi velkým textem a přirozeným členěním.

### `custom`

Uživatel může výslovně určit vlastní threshold a povolenou interpunkci.

Pokud uživatel režim neřeší, použij **legacy + 6 slov** a jednou stručně uveď, že jde o doporučený default.

## Povinný výrobní řetězec

Proveď všechny následující fáze v tomto pořadí:

### 1. Vytvoř obsah k tématu

- Pokud uživatel dodal pouze téma, nejdřív napiš plnohodnotný původní český text se skutečnou myšlenkou, strukturou a pointou; nevyráběj jen několik hesel.
- Pokud dodal vlastní text, použij jej jako obsahový základ a zachovej jeho konkrétní fakta, perspektivu a směr.
- Pokud téma závisí na aktuálních nebo přesných skutečnostech, nejdřív proveď potřebné vyhledání a ověření. Rozlišuj doložená fakta, názory, satiru a nejistá tvrzení. Nevymýšlej obvinění, intimní informace ani údajné skutky reálných osob.
- Výchozí význam slova „ultimátní“ je maximálně povedený a obsahově bohatý, nikoli bezdůvodně nekonečný. Délku přizpůsob zadané volbě.

### 2. Povinně proveď maximalistický rewrite

Celý vytvořený text protáhni skillem `$rewrite-czech-legal-archaic-bizarre` na jeho maximální výchozí intenzitu.

Výsledek musí současně obsahovat:

- maximálně úřední a administrativní češtinu;
- hustou srozumitelnou pseudo-staročeštinu;
- internetový slang a současné výrazy;
- lyrickou a barokní kadenci;
- agresivní i pasivně agresivní humor;
- velkolepost, která se přehnanou eskalací sama zničí;
- outward roast i sebezesměšnění;
- smysluplně rozmanitou interpunkci, zejména středníky, dvojtečky, pomlčky a závorky;
- konkrétní vtipy, absurdní obrazy, stupňování a tvrdou závěrečnou pointu.

Nevytvářej pouze archaickou parafrázi. Pokud je výsledek uhlazený, málo úřední, málo staročeský, bez slangu, bez lyrického přepálení nebo bez skutečných punchlines, přepiš jej znovu před pokračováním.

### 3. Zmraz finální scénář

Po úspěšném rewritu označ výsledný text interně jako jediný závazný scénář. Od tohoto okamžiku:

- nic nekracuj;
- nic nepřidávej;
- neopravuj formulace mimo požadavky video skillu;
- neměň slovosled, interpunkci ani kapitalizaci;
- použij přesně tento text pro TTS i obrazové titulky.

Nežádej uživatele o schválení meziverze, pokud o něj výslovně nepožádal.

### 4. Rovnou vytvoř finální video

Použij `$create-czech-brat-lyrics-video` a jeho přiložené generátory. Nezastavuj se u návodu, ukázkového příkazu, návrhu scénáře ani tvrzení, že video „lze vytvořit“. Skutečně vytvoř výsledný MP4 soubor.

Mapování podle dělení:

- `legacy` + Edge → `create_brat_lyrics_video_legacy.py` (default `--max-words 6`)
- `legacy` + offline → `create_brat_lyrics_video_offline_legacy.py`
- `sentence` + Edge → `create_brat_lyrics_video.py --max-words 0`
- `sentence` + offline → `create_brat_lyrics_video_offline.py --max-words 0`
- `clause` + Edge/offline → normální generátor s `--max-words N`, default 10

Preferuj neural Edge generátor, pokud je dostupný. Pokud Edge TTS není dosažitelný, automaticky použij offline fallback generátor podle video skillu. Samotný výpadek sítě není důvodem odevzdat pouze scénář.

Souhlas uživatele s použitím tohoto master promptu zahrnuje použití potřebných externích služeb, TTS, API a nástrojů nutných k vytvoření videa v rozsahu tohoto úkolu. Nezahrnuje veřejné publikování videa ani jiné nesouvisející externí akce.

### 5. Proveď povinnou kontrolu úplnosti

Před odevzdáním ověř všechna pravidla video skillu a zejména:

- `source_words == displayed_words`;
- každé slovo závazného scénáře je přesně jednou obsaženo v titulcích;
- u Edge TTS ověř skutečné WordBoundary časování;
- u offline TTS přiznej `timing_mode: estimated-from-offline-audio` a ověř přesné pokrytí zdrojových tokenů;
- žádné slovo nezmizelo, nebylo zdvojeno ani přesunuto;
- hranice textových bloků přesně odpovídají zvolenému `Dělení`;
- obraz má 1080 × 1080, 30 fps, H.264 video a AAC audio;
- pozadí odpovídá zvolené variantě;
- reportovaný hlas/backend odpovídá tomu, co bylo skutečně použito;
- video obsahuje zvuk i obraz a jeho délka odpovídá TTS.

Při jakémkoli nesouladu video oprav a zkontroluj znovu. Neodevzdávej částečný nebo neověřený výsledek, pokud je v prostředí funkční některý podporovaný český TTS backend.

## Výstup

Odevzdej:

1. odkaz ke stažení hotového MP4;
2. přesný finální scénář použitý ve videu;
3. jednu krátkou řádku s požadovaným hlasem, skutečně použitým TTS backendem/hlasem, pozadím, režimem dělení, thresholdem, režimem časování a výsledkem kontroly slov.

Nevypisuj interní mezikroky, pracovní draft ani dlouhé vysvětlování.

## Nejkratší použití

```text
Téma: destilovaná voda
Hlas: Vlasta
Pozadí: brat-green
Dělení: legacy
Délka: dlouhá
```

Celá věta:

```text
Téma: destilovaná voda
Hlas: Vlasta
Pozadí: white
Dělení: sentence
```

Kompromis:

```text
Téma: destilovaná voda
Hlas: espeak:cs
Pozadí: white
Dělení: clause
Max slov: 10
```
