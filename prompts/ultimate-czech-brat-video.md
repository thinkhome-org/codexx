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
Hlas: [Antonín | Vlasta | vlastní Edge TTS ID]
Pozadí: [white | brat-green | #RRGGBB]
Délka: [krátká | střední | dlouhá | vlastní požadavek]
Doplňující pokyny: [volitelné]
```

Uživatel může napsat jen `Téma: ...`. Pokud téma chybí, zeptej se pouze na téma. Pokud chybí hlas nebo pozadí, polož jednu společnou krátkou otázku na obě volby, jak vyžaduje video skill; nikdy automaticky nevybírej Antonína ani bílé pozadí. Pokud uživatel výslovně napíše, že volbu nechává na tobě, vyber vhodnou kombinaci sám.

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

Použij `$create-czech-brat-lyrics-video` a jeho přiložený generátor. Nezastavuj se u návodu, ukázkového příkazu, návrhu scénáře ani tvrzení, že video „lze vytvořit“. Skutečně vytvoř výsledný MP4 soubor.

Souhlas uživatele s použitím tohoto master promptu zahrnuje použití potřebných externích služeb, TTS, API a nástrojů nutných k vytvoření videa v rozsahu tohoto úkolu. Nezahrnuje veřejné publikování videa ani jiné nesouvisející externí akce.

### 5. Proveď povinnou kontrolu úplnosti

Před odevzdáním ověř všechna pravidla video skillu a zejména:

- `source_words == displayed_words`;
- každé slovo závazného scénáře je přesně jednou vysloveno a přesně jednou obsaženo v titulcích;
- žádné slovo nezmizelo, nebylo zdvojeno ani přesunuto;
- věta se bez výslovného důvodu nepřerušila uprostřed;
- obraz má 1080 × 1080, 30 fps, H.264 video a AAC audio;
- hlas a pozadí odpovídají zvolené variantě;
- video obsahuje zvuk i obraz a jeho délka odpovídá TTS.

Při jakémkoli nesouladu video oprav a zkontroluj znovu. Neodevzdávej částečný nebo neověřený výsledek.

## Výstup

Odevzdej:

1. odkaz ke stažení hotového MP4;
2. přesný finální scénář použitý ve videu;
3. jednu krátkou řádku s použitým hlasem, pozadím a výsledkem kontroly slov.

Nevypisuj interní mezikroky, pracovní draft ani dlouhé vysvětlování.

## Nejkratší použití

Do nového chatu vlož odkaz na tento soubor a za něj napiš například:

```text
Téma: destilovaná voda
Hlas: Vlasta
Pozadí: brat-green
Délka: dlouhá
```
