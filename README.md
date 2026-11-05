# Teknikat e Painformuara të Kërkimit

Implementimi në Python i problemeve Social Golfers, Sudoku dhe Latin Square, së bashku me pemët e vizatuara në fletë për 8-Puzzle, Missionaries and Cannibals dhe Rotating Workforce Scheduling.

## Pjesët e implementuara

| # | Problemi | Metoda | Skedari |
| --- | --- | --- | --- |
| 1 | Social Golfers | DFS me Backtracking | `1_social_golfers/social_golfers.py` |
| 2 | Sudoku: Easy, Medium, Hard | BFS me ruajtje të prindërve; backtracking rekursiv veçmas | `2_sudoku/sudoku_bfs.py` |
| 3 | Latin Square | IDDFS me Backtracking | `3_latin_square/latin_square_iddfs.py` |
| 4 | Pemët e kërkimit | Vizatim në fletë, i ruajtur si PDF | `4_search_trees/` |

## Struktura e projektit

```text
1_social_golfers/
    social_golfers.py
2_sudoku/
    sudoku_bfs.py
3_latin_square/
    latin_square_iddfs.py
4_search_trees/
    8_Puzzles.pdf
    Missionaries_and_Cannibals.pdf
    Rotating_Workforce_Scheduling.pdf
.gitignore
README.md
app.py
```

## Kërkesat për ekzekutim

Python 3.10 ose më i ri. Nuk nevojiten biblioteka shtesë.

## Ekzekutimi i projektit

```bash
python3 app.py
```

Kjo komandë ekzekuton tri zgjidhësit dhe shfaq vendndodhjen e PDF-ve të pemëve. Për ta zgjedhur një pjesë veçmas:

```bash
python3 app.py --task golfers
python3 app.py --task sudoku
python3 app.py --task latin
python3 app.py --task trees
```

## 1. Social Golfers

Planifikohen n = g × p lojtarë në g grupe me nga p lojtarë për w javë, pa luajtur asnjë çift bashkë më shumë se një herë.

- **Variablat:** X[java, lojtari], me domain të grupeve {0, ..., g-1}.
- **Kufizimet:** çdo lojtar luan një herë në javë, çdo grup ka p lojtarë dhe asnjë çift nuk përsëritet.
- **Funksioni objektiv:** minimizon takimet e përsëritura të çifteve; një orar i plotë dhe i vlefshëm ka penalitet 0.
- **Landscape:** g^(n×w) vendosje pa kufizime. Në një javë ka P = n! / ((p!)^g × g!) ndarje në grupe pa renditje; P^w numëron oraret kandidate që respektojnë kapacitetin, përpara kontrollit të çifteve.
- **Algoritmi:** DFS me Backtracking. Kur një vendosje dështon, hiqen lojtari dhe çiftet e shtuara nga ai veprim.

```bash
python3 1_social_golfers/social_golfers.py --groups 8 --size 4 --weeks 3
```

Demonstrimi gjen një orar trejavor për 32 lojtarë. Kufiri teorik është floor((n-1)/(p-1)), pra 10 javë për grupe me nga katër lojtarë. Një orar referencë dhjetëjavor, me burimin e shënuar, ruhet brenda skedarit dhe verifikohet nga `app.py`; ai nuk është rezultat i demonstrimit tonë DFS.

### Rezultatet

| Rasti | Rezultati | Nyje të zgjeruara | Kthime prapa | Koha (s) |
| --- | --- | ---: | ---: | ---: |
| 32 lojtarë, 8 grupe me nga 4, 3 javë | Orar i vlefshëm nga DFS; funksioni objektiv = 0 | 66 | 0 | 0.000261 |
| Orari referencë dhjetëjavor | U verifikuan pjesëmarrja dhe çiftet pa përsëritje | — | — | — |

Orari trejavor është rezultati i matur i DFS-it. Dhjetë javë është maksimumi për rastin fillestar, sepse orari referencë e arrin kufirin e sipërm. Demonstrimi DFS nuk e kërkon ose provon vetë këtë maksimum.

## 2. Sudoku Solver

Zgjidhen shembuj të niveleve Easy, Medium dhe Hard, duke ruajtur të gjithë numrat fillestarë.

- **Variablat:** qelizat bosh, me domain nga {1, ..., 9}; tabela ruhet si tuple me 81 numra të plotë dhe 0 shënon qelizën bosh.
- **Kufizimet:** asnjë numër nuk përsëritet në rresht, kolonë ose kuti 3×3.
- **Funksioni objektiv:** numri i qelizave bosh plus penalitetet për vlera të përsëritura në 27 njësitë.
- **Landscape:** për m qeliza bosh ka 9^m vendosje pa kufizime dhe (9^(m+1)-1)/8 nyje në pemën pa prerje. Produkti i madhësive të domain-eve fillestare jep një kufi më të ngushtë.
- **Algoritmi:** BFS me radhë FIFO dhe ruajtje të prindërve. DFS me Backtracking rekursiv ofrohet veçmas. Si parazgjedhje plotësohen edhe qelizat që kanë vetëm një kandidat të lejuar; ky deduksion nuk rendit zgjedhjet e kërkimit.

```bash
python3 2_sudoku/sudoku_bfs.py --level easy
python3 2_sudoku/sudoku_bfs.py --level medium
python3 2_sudoku/sudoku_bfs.py --level hard
python3 2_sudoku/sudoku_bfs.py --level hard --method dfs
python3 2_sudoku/sudoku_bfs.py --level easy --no-propagation
```

Ndjekja e lidhjeve me prindërit rindërton rrugën e zgjidhjes së BFS-it; kjo ndryshon nga backtracking rekursiv klasik. Me `--no-propagation`, çdo hark i kërkimit plotëson vetëm një qelizë.

### Rezultatet

BFS me deduksionin e qelizave me një kandidat të aktivizuar:

| Niveli | Numra fillestarë | Qeliza bosh | Nyje të zgjeruara | Madhësia maksimale e radhës | Koha (s) | Funksioni objektiv në fund |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Easy | 30 | 51 | 1 | 1 | 0.000770 | 0 |
| Medium | 28 | 53 | 19 | 5 | 0.010985 | 0 |
| Hard | 23 | 58 | 120 | 26 | 0.111787 | 0 |

Të tri tabelat zgjidhen dhe numrat fillestarë ruhen. Easy plotësohet nga deduksionet fillestare, prandaj BFS përpunon vetëm një gjendje. Nivelet e tjera kërkojnë edhe degëzim; numërimet i përkasin këtij implementimi me deduksione, jo BFS-it pa to.

| Niveli | Vendosje pa kufizime |
| --- | --- |
| Easy | 9^51 |
| Medium | 9^53 |
| Hard | 9^58 |

## 3. Latin Square

Ndërtohet një tabelë n×n ku numrat nga 1 deri në n paraqiten saktësisht një herë në çdo rresht dhe kolonë.

- **Variablat:** n² qeliza, secila me domain {1, ..., n}; 0 shënon qelizën bosh.
- **Kufizimet:** vlerat në çdo rresht dhe kolonë duhet të jenë të ndryshme.
- **Funksioni objektiv:** qelizat bosh plus përsëritjet në rreshta dhe kolona.
- **Landscape:** n^(n²) vendosje të plota pa kufizime dhe sum(n^k, k=0..n²) nyje në pemën pa prerje.
- **Algoritmi:** IDDFS me Backtracking, me kufij thellësie nga 0 deri në n². Rreshti dhe kolona e parë fiksohen për të shmangur konfigurime ekuivalente.

```bash
python3 3_latin_square/latin_square_iddfs.py 5
```

### Rezultatet

| n | Iteracione | Kufijtë e thellësisë | Nyje të zgjeruara | Kthime prapa | Koha (s) | Funksioni objektiv në fund |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| 3 | 10 | 0–9 | 60 | 41 | 0.000056 | 0 |
| 5 | 26 | 0–25 | 6761 | 6710 | 0.005099 | 0 |

Rreshti dhe kolona e parë kufizohen nga thyerja e simetrisë, por plotësohen ende qelizë pas qelize. Prandaj për n=5 përdoren kufijtë 0 deri në 25 dhe gjithsej 26 iteracione. IDDFS përsërit kërkimet derisa kufiri të lejojë plotësimin e të gjithë tabelës.

Katrori 5×5 i gjeneruar është:

```text
1 2 3 4 5
2 1 4 5 3
3 4 5 1 2
4 5 2 3 1
5 3 1 2 4
```

Çdo rresht dhe kolonë përmban numrat nga 1 deri në 5 saktësisht një herë.

## 4. Pemët e kërkimit të vizatuara në fletë

Pemët janë vizatuar në fletë dhe janë përfshirë si PDF të skanuara. Kryqi shënon gjendjen e pavlefshme, ndërsa shenja e kthimit tregon një gjendje të përsëritur; këto gjendje nuk zgjerohen përsëri.

### 8-Puzzle - [8_Puzzles.pdf](4_search_trees/8_Puzzles.pdf)

| Elementi | Përshkrimi |
| --- | --- |
| Gjendja | Tabelë 3×3 me pllakat 1–8 dhe një vend bosh |
| Fillestare | `1 2 3 / 4 _ 6 / 7 5 8` |
| Qëllimi | `1 2 3 / 4 5 6 / 7 8 _` |
| Veprimet | Vendi bosh lëviz Up, Down, Left ose Right |

Pema ndjek nivelet e BFS-it. Lëvizja që e kthen menjëherë vendin bosh te prindi nuk vizatohet. Qëllimi arrihet në thellësinë 2 me **Down → Right**.

### Missionaries and Cannibals - [Missionaries_and_Cannibals.pdf](4_search_trees/Missionaries_and_Cannibals.pdf)

| Elementi | Përshkrimi |
| --- | --- |
| Gjendja | `(M, K, B)`: misionarët dhe kanibalët në bregun e majtë, plus ana e varkës; K shënon kanibalët në vizatim |
| Fillestare | `(3,3,L)` |
| Qëllimi | `(0,0,R)` |
| Ana e varkës | L = majtas; R = djathtas |
| Veprimet | Varka mbart `1M`, `2M`, `1K`, `2K` ose `1M + 1K` |
| Rregulli | Në asnjë breg kanibalët nuk duhet të jenë më shumë se misionarët, kur ka misionarë |

Varka mbart një ose dy persona dhe nuk lëviz bosh. Pema ndjek nivelet e BFS-it; gjendjet e pavlefshme dhe të përsëritura nuk zgjerohen përsëri. Qëllimi arrihet në thellësinë 11, me **11 kalime**.

### Rotating Workforce Scheduling - [Rotating_Workforce_Scheduling.pdf](4_search_trees/Rotating_Workforce_Scheduling.pdf)

Përdoret një shembull i vogël, që pema të paraqitet lehtë në fletë.

| Elementi | Përshkrimi |
| --- | --- |
| Shembulli | Tre punëtorë (rreshtat), tri ditë (kolonat) |
| Kërkesa ditore | Një `D` (turni i ditës), një `N` (turni i natës) dhe një `-` (pushim) |
| Rregulli | Pas `N` nuk lejohet `D` ditën pasuese; në interpretimin rrotullues, kjo vlen edhe nga dita e fundit e një rreshti te dita e parë e tjetrit, përfshirë rreshtin e fundit te i pari |
| Gjendja | Orari i plotësuar pjesërisht, ditë pas dite |
| Fillestare | Orari bosh |
| Veprimi | Zgjidhen turnet e ditës së radhës për të tre punëtorët: gjashtë permutacione të mundshme |
| Qëllimi | Të tri ditët të plotësohen pa kalimin e ndaluar `N → D` |

Në çdo nivel të paraqitur zgjerohet vetëm nyja e parë e vlefshme e zgjedhur. Nyjat e tjera shfaqen si alternativa ose gjendje të refuzuara, prandaj kjo është pemë e pjesshme. Një zgjidhje e vlefshme është:

```text
D D D
N N N
- - -
```

Çdo ditë ka një turn dite, një turn nate dhe një punëtor në pushim. Kufijtë ndërmjet rreshtave janë `D → N`, `N → -` dhe `- → D`, kështu që ky model e plotëson edhe rregullin e kalimit ndërmjet rreshtave. Kjo është një zgjidhje e realizueshme sipas këtyre rregullave; shpërndarja e barabartë e turneve nuk kërkohet në këtë shembull.

## Testet

Testet janë brenda tre skedarëve Python; nuk ka skedarë të veçantë testimi:

```bash
python3 app.py --test
```

**23 testet e zgjidhësve** kontrollojnë zgjidhjet e vlefshme, çiftet e golfit pa përsëritje, ruajtjen e numrave fillestarë të Sudoku-t, rrugët e BFS-it, Backtracking, kufijtë e IDDFS, llogaritjet e landscape, hyrjet e pavlefshme dhe kufijtë e burimeve. Rezultati `limit` do të thotë se kërkimi është ndalur pa vendim; nuk provon se problemi nuk ka zgjidhje.

## Interpretimi i rezultateve

Kohët janë nga një ekzekutim lokal dhe mund të ndryshojnë sipas kompjuterit ose ekzekutimit. `expanded` numëron gjendjet e përpunuara pasi kalojnë kontrollin e kufirit të burimeve; `backtracks` numëron vendosjet e anuluara. Madhësitë e landscape numërojnë hapësira të relaksuara kandidatësh, jo numrin e zgjidhjeve të vlefshme.
