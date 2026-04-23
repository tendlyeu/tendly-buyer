# Tendly ostja AI tööriistad — kasutajalood ja küsimustik

> **Eesmärk:** See dokument defineerib kasutajalood ja valideerimisküsimused Tendly Agent Chat platvormi laiendamiseks ostja-poolsete AI tööriistadega. Ostjad (hankespetsialistid, hankijad) kasutavad neid tööriistu hankedokumentide koostamiseks, hindade võrdluseks ja hankimise ettevalmistamiseks — kõik läbi vestlusliidese koos kanvaa-paneeli kuvamisega.
>
> **Kasutamine:** Vaadake iga osa läbi, hinnake kasutajalugusid MoSCoW prioriteediskaalal ja vastake küsimustiku küsimustele nõuete valideerimiseks.

---

## 1. Kasutajapersoonad

| ID | Persoon | Kirjeldus |
|----|---------|-----------|
| B1 | Hankespetsialist | Igapäevane ostja, kes koostab hankeid, haldab hankeprotsesse ja hindab pakkumusi. Peamine kasutaja RFP koostamise ja hinnavõrdluse tööriistadele. |
| B2 | Hankejuht | Vanemostja, kes juhib hankestrateegiaid, kinnitab hankeid ja tagab vastavuse hankeregulatsioonidele (EL direktiivid, riigisisene õigus). |
| B3 | Eelarve omanik / osakonnajuht | Sisemine sidusrühm, kes defineerib vajadused, seab eelarved ja kinnitab hankeplaane. Vajab turuluure andmeid eelarve planeerimiseks. |
| B4 | Jurist / vastavusspetsialist | Vaatab üle hankedokumendid õiguspärasuse osas, kontrollib hindamiskriteeriumide õiglust ja tagab riigihangete seaduse järgimise. |
| B5 | Finantskontrolör | Valideerib kuluhinnangu, kontrollib eelarve jaotust, jälgib lepingukulusid ja tagab finantsnõuetele vastavuse. |
| B6 | Tehniline spetsialist | Valdkonna ekspert, kes defineerib tehnilised nõuded, spetsifikatsioonid ja hindamiskriteeriumid spetsiifiliste hangete jaoks (IT, ehitus, meditsiin). |

### Küsimustik: Persoonad

- **Q1.1** Millised neist persoonidest eksisteerivad teie organisatsioonis? Kas on veel rolle, kes on hankeprotsessiga seotud?
- **Q1.2** Kes algatab tavaliselt uue hankeprotsessi — eelarve omanik (B3) või hankespetsialist (B1)?
- **Q1.3** Mitu inimest on tavaliselt kaasatud ühe hankedokumendi koostamisse?
- **Q1.4** Kas kasutate praegu mõnda AI- või digiriista hangete koostamiseks? Kui jah, siis milliseid?

---

## 2. Hankedokumendi koostamine AI-ga

| ID | Kasutajalugu | Persoon |
|----|-------------|---------|
| US-01 | Hankespetsialistina tahan kirjeldada oma hanke vajadust vabas vormis, et AI koostaks struktureeritud hankedokumendi mustandi, mis põhineb parimail praktikal ja regulatiivsetel nõuetel. | B1 |
| US-02 | Hankespetsialistina tahan, et AI pakuks välja sobivad hindamiskriteeriumid ja kaalud vastavalt hanke tüübile (teenused, asjad, ehitustööd), et ma koostaksin õiglased ja tõhusad kriteeriumid. | B1 |
| US-03 | Hankejuhina tahan valida hankedokumendi mallidest (avatud hankemenetlus, piiratud menetlus, läbirääkimistega menetlus), et koostatud dokument järgiks õiget hankeprotseduuri. | B2 |
| US-04 | Hankespetsialistina tahan, et AI genereeriks sobivad CPV koodid minu vajaduse kirjeldusest, et hange oleks õigesti klassifitseeritud ja jõuaks õigete pakkujateni. | B1 |
| US-05 | Hankespetsialistina tahan, et AI koostaks kvalifitseerimistingimused (kogemus, finantsseisund, tehniline suutlikkus) vastavalt lepingu eeldatavale maksumusele ja tüübile, et nõuded oleksid proportsionaalsed ja mittediskrimineerivad. | B1 |
| US-06 | Juristina tahan, et AI tuvastaks võimalikud vastavusprobleemid hankedokumendi mustandis (diskrimineerivad nõuded, puuduvad kohustuslikud klauslid, valed piirmäärad), et saaksin need enne avaldamist parandada. | B4 |
| US-07 | Hankespetsialistina tahan hankedokumenti vestluses itereerida — paludes AI-l muuta jaotisi, lisada klausleid või sõnastada nõudeid ümber — et viimistleksin dokumenti vestluslikult. | B1 |
| US-08 | Eelarve omanikuna tahan esitada kõrgtasemelisi vajadusi ("vajame kontori renoveerimist 200 inimesele") ja lasta AI-l need laiendada detailseteks tehnilisteks spetsifikatsioonideks, et mul poleks vaja hanke ekspertiisi protsessi alustamiseks. | B3 |
| US-09 | Hankespetsialistina tahan eksportida lõplikku hankedokumenti allalaaditava failina (DOCX/PDF) kanvaa-paneelilt, et saaksin selle üles laadida hankeportaali. | B1 |
| US-10 | Hankejuhina tahan, et AI koostaks hanke ajagraafiku (teate periood, pakkumuste esitamise tähtaeg, hindamisperiood, lepingu sõlmimine) vastavalt menetluse tüübile ja EL piirmääradele, et seaksin realistlikud tähtajad. | B2 |

### Küsimustik: Hankedokumendi koostamine

- **Q2.1** Milline on teie praegune hankedokumendi koostamise protsess? Kui kaua kulub tavaliselt nõuetest kuni avaldamiseni?
- **Q2.2** Millised hankedokumendi osad on kõige aeganõudvamad kirjutada? (nt tehnilised spetsifikatsioonid, hindamiskriteeriumid, kvalifitseerimistingimused)
- **Q2.3** Kas kasutate standardseid malle? Kui jah, kas need on organisatsiooni-spetsiifilised või riiklikud mallid?
- **Q2.4** Kui sageli tuleb avaldatud hankeid parandada vigade või puuduste tõttu hankedokumendis?
- **Q2.5** Kas usaldaksite AI loodud esimest mustandit, mida te seejärel üle vaatate ja muudate, või eelistate AI-d assistendina, mis pakub valikuid?
- **Q2.6** Milliseid hankemenetlusi kasutate kõige sagedamini? (Avatud, piiratud, läbirääkimistega, konkurentsipõhine dialoog, innovatsioonipartnerlus)
- **Q2.7** Milliseid keeli peaks hankedokumendi koostamine toetama? (Eesti, inglise, mõlemad?)

---

## 3. Turuhinnaluure — kinnisvara

| ID | Kasutajalugu | Persoon |
|----|-------------|---------|
| US-11 | Eelarve omanikuna tahan otsida ajaloolistest hankeandmetest kontoriruumide üürihindu ruutmeetri kohta linna ja piirkonna lõikes, et seada realistlik eelarve meie ruumivajadusele. | B3 |
| US-12 | Hankespetsialistina tahan, et AI näitaks mulle võrreldavaid kinnisvarahankeid (kontoriruum, hooldus, koristus) minu piirkonnas, et mõistaksin kehtivaid turuhindu. | B1 |
| US-13 | Finantskontrolörina tahan näha hinnatrende aja jooksul kinnisvarateenuste osas (üür, hooldus, renoveerimine), et prognoosida kulusid mitmeaastase eelarve planeerimiseks. | B5 |
| US-14 | Hankespetsialistina tahan, et AI pakuks eeldatava maksumuse vahemiku minu kinnisvarahankele vastavalt asukohale, pindalale, kestusele ja teenuse tasemele, et seada proportsionaalne lepingumaksumus. | B1 |
| US-15 | Eelarve omanikuna tahan võrrelda avaliku ja erasektori üürihindu konkreetses asukohas, et mõista, kas hanke tee pakub raha eest väärtust. | B3 |

### Küsimustik: Kinnisvara hinnastamine

- **Q3.1** Milliseid kinnisvarahankeid te kõige sagedamini teete? (Kontori üür, hooldus, koristus, renoveerimine, ehitus)
- **Q3.2** Millised andmepunktid on kinnisvara hinnavõrdluse jaoks kõige olulisemad? (Hind m² kohta, lepingu kogumaksumus, kestus, asukoht, teenuse tase)
- **Q3.3** Kas kasutate praegu mõnda võrdlusandmestikku eeldatavate maksumuste seadmiseks kinnisvarahangetes? Kui jah, siis milliseid allikaid?
- **Q3.4** Kui kindel olete praegu eeldatavates maksumustes, mida seate kinnisvarahangetele? (Väga kindel / Mõnevõrra / Ei ole kindel)
- **Q3.5** Kas ajaloolised hankeandmed (võidetud lepingud, tegelikud kulud) oleksid kasulikumad kui turu-uuringud?

---

## 4. Turuhinnaluure — personal

| ID | Kasutajalugu | Persoon |
|----|-------------|---------|
| US-16 | Eelarve omanikuna tahan otsida tüüpilisi tunnipalgamäärasid ja päevamäärasid erinevate ametirollide jaoks (arendajad, projektijuhid, konsultandid, turvamehed) riigihangetes, et planeerida eelarvet õigesti. | B3 |
| US-17 | Hankespetsialistina tahan, et AI näitaks mulle võrreldavaid personalihankeid (ajutine tööjõud, konsultatsioonid, sisseostetud teenused) koos lepingumaksumuste ja meeskonna koosseisudega, et võrdleksin oma nõudeid. | B1 |
| US-18 | Tehnilise spetsialistina tahan otsida tüüpilisi kvalifitseerimistingimusi IT-personalihangete jaoks (kogemuse aastad, sertifikaadid, turvaload), et seada nõuded, mis on saavutatavad, kuid säilitavad kvaliteedi. | B6 |
| US-19 | Finantskontrolörina tahan võrrelda personalikulusid riikide lõikes (Eesti, Läti, Leedu, Poola) samade rollitüüpide jaoks, et mõista regionaalseid kuluerinevusi piiriüleste hangete jaoks. | B5 |
| US-20 | Hankespetsialistina tahan, et AI pakuks hinnaskoorimise valemit (madalaim hind, parim hinna-kvaliteedi suhe, kuluefektiivsus) vastavalt personalitarne tüübile, et hindamismeetod oleks asjakohane. | B1 |

### Küsimustik: Personali hinnastamine

- **Q4.1** Milliseid personali- ja tööjõuhankeid te teete? (IT-konsultandid, ajutised töötajad, koristusteenuse personal, turvateenistus, erialateenused)
- **Q4.2** Kas kasutate personalihangetes tunnimäärasid, päevamäärasid või lepingu kogumaksumust?
- **Q4.3** Mis on personalihangete hinnastamise juures kõige keerulisem? (Määrade seadmine, rollide defineerimine, mahu prognoosimine, kvaliteedi hindamine)
- **Q4.4** Kas peate personalimäärade ootuste seadmisel arvestama miinimumpalga regulatsioonide või kollektiivlepingutega?
- **Q4.5** Kas teiste avaliku sektori organisatsioonide võidetud lepingute võrdlusandmed oleksid kasulikud?

---

## 5. Turuhinnaluure — seadmed

| ID | Kasutajalugu | Persoon |
|----|-------------|---------|
| US-21 | Eelarve omanikuna tahan otsida tüüpilisi IT-seadmete kulusid (serverid, tööjaamad, võrguseadmed, tarkvaralitsentsid) riigihangetes, et koostada täpseid eelarveid. | B3 |
| US-22 | Hankespetsialistina tahan, et AI näitaks võrreldavaid seadmehankeid (meditsiiniseadmed, sõidukid, laboriinstrumendid, kontormööbel) koos spetsifikatsioonide ja hindadega, et võrdleksin meie nõudeid. | B1 |
| US-23 | Tehnilise spetsialistina tahan otsida tehnilisi spetsifikatsioone, mida kasutati sarnastes seadmehangetes, et koostada spetsifikatsioonid, mis on konkurentsivõimelised, kuid ei piira ühte tarnijat. | B6 |
| US-24 | Finantskontrolörina tahan võrrelda ostu- ja liisingukulusid seadmekategooriate lõikes, et soovitada kõige kuluefektiivsemat hankimisviisi. | B5 |
| US-25 | Hankespetsialistina tahan, et AI tuvastaks, kui minu seadmete spetsifikatsioonid on liiga piiravad (osutavad ühele brändile/tarnijale) ja pakuks alternatiive, et järgida mittediskrimineerimise põhimõtet. | B1 |

### Küsimustik: Seadmete hinnastamine

- **Q5.1** Milliseid seadmekategooriaid te kõige sagedamini hangite? (IT-riistvara, tarkvara, meditsiiniseadmed, sõidukid, kontormööbel, laboriseadmed)
- **Q5.2** Kas tavaliselt ostate otse või kasutate liisingu-/rendilepinguid?
- **Q5.3** Kuidas te praegu seadmekulusid hindate? (Tarnijapakkumised, turu-uuring, ajaloolised andmed, kataloogid)
- **Q5.4** Kas teil on kunagi hange vaidlustatud liiga piiravate spetsifikatsioonide tõttu? Kuidas see lahendati?
- **Q5.5** Kas AI tööriist, mis kontrollib spetsifikatsioone brändi-spetsiifilisuse osas, oleks väärtuslik?

---

## 6. Hinnavõrdlus ja analüütika

| ID | Kasutajalugu | Persoon |
|----|-------------|---------|
| US-26 | Hankespetsialistina tahan, et AI koostaks hinnavõrdluse raporti minu planeeritud hanke jaoks — võrreldes sarnaseid ajaloolisi lepinguid CPV koodi, riigi ja väärtuse vahemiku järgi — et põhjendada eeldatavat maksumust. | B1 |
| US-27 | Hankejuhina tahan näha turuanalüüsi kanvaa-artefakti, mis näitab hinnajaotusi, võitjate mustreid ja konkurentsitasemeid minu hankekategooria jaoks, et teha andmepõhiseid otsuseid. | B2 |
| US-28 | Finantskontrolörina tahan eksportida võrdlusandmeid raportina (PDF), mida saan lisada hanketoimikusse eeldatava lepingumaksumuse põhjendamiseks. | B5 |
| US-29 | Eelarve omanikuna tahan, et AI hoiataks mind, kui minu eeldatav eelarve on oluliselt kõrgem või madalam kui turuhinnad sarnaste hangete jaoks, et kohandaksin enne avaldamist. | B3 |
| US-30 | Hankespetsialistina tahan küsida AI-lt "mis on õiglane hind X-i eest?" ja saada vastus, mis põhineb tegelikel hankeandmetel koos allikatega, et mul oleks tõenduspõhine hinnastamine. | B1 |

### Küsimustik: Hinnavõrdlus

- **Q6.1** Kuidas te praegu põhjendate eeldatavat lepingumaksumust oma hangetes? (Turu-uuring, tarnijapakkumised, ajaloolised andmed, eksperdi arvamus)
- **Q6.2** Kas teil on kunagi olnud hange, kus eeldatav maksumus oli oluliselt vale? Milline oli mõju?
- **Q6.3** Kas peaksite väärtuslikuks automaatset võrdlust sarnaste lepingutega teistes riikides?
- **Q6.4** Kui oluline on, et hinnavõrdluse andmed sisaldavad allikate viiteid (lingid tegelikele hangetele)?
- **Q6.5** Kas vajate võrdlusandmeid reaalajas või piisaks igakuisest uuendatud andmestikust?

---

## 7. Vastavus ja kvaliteedikontroll

| ID | Kasutajalugu | Persoon |
|----|-------------|---------|
| US-31 | Juristina tahan, et AI valideeriks, et minu hankedokument vastab EL hanke direktiividele (2014/24/EL, 2014/25/EL) ja riigihangete seadusele, et vähendada õiguslikku riski. | B4 |
| US-32 | Hankespetsialistina tahan, et AI kontrolliks, et hindamiskriteeriumid on proportsionaalsed lepingu maksumusega (pole üle-kvalifitseerimist), et maksimeerida konkurentsi ja vältida kaebusi. | B1 |
| US-33 | Hankejuhina tahan, et AI hindaks eeldatavat pakkujate arvu ajalooliste andmete põhjal sarnaste hangete kohta minu piirkonnas, et seada realistlikud ootused. | B2 |
| US-34 | Juristina tahan, et AI koostaks vastavuse kontrollnimekirja minu hankemenetluse jaoks (kohustuslikud teated, ooteperiood, dokumentatsiooni nõuded), et ma ei jätaks ühtegi sammu vahele. | B4 |
| US-35 | Hankespetsialistina tahan, et AI vaataks üle minu hindamiskriteeriumid ja tuvastaks, kas hinna osakaal on sarnaste hangetega võrreldes liiga kõrge või madal, et järgiksin turgu norme. | B1 |

### Küsimustik: Vastavus

- **Q7.1** Millistele hankeregulatsioonidele peate vastama? (EL direktiivid, riigihangete seadus, sisemised eeskirjad)
- **Q7.2** Millised on teie organisatsiooni hangetes kõige levinumad vastavusvead?
- **Q7.3** Kui sageli vaidlustavad pakkujad teie hankeid? Millised on tüüpilised alused?
- **Q7.4** Kas kasutaksite AI vastavuskontrolli enne hanketeate avaldamist?
- **Q7.5** Kas vajate tuge nii ülekünniseliste (EL) kui allapoole piirmäära (riiklike) menetluste jaoks?

---

## 8. AI vestlusliides ostjatele

| ID | Kasutajalugu | Persoon |
|----|-------------|---------|
| US-36 | Hankespetsialistina tahan alustada vestlust "Mul on vaja hankida [X]" ja lasta AI-l juhtida mind kogu protsessi — nõuetest kuni hankedokumendi mustandini — samm-sammult. | B1 |
| US-37 | Eelarve omanikuna tahan küsida "Kui palju peaksime eelarvestama [hanke tüübi] jaoks?" ja saada AI vastuse, mis põhineb ajaloolistel hankeandmetel kanvaa-paneelil. | B3 |
| US-38 | Hankespetsialistina tahan üles laadida olemasoleva hankedokumendi ja paluda AI-l see üle vaadata terviklikkuse ja vastavuse probleemide osas, mis kuvatakse kanvaa-artefaktina. | B1 |
| US-39 | Hankejuhina tahan, et vestlusajalugu säiliks, et saaksin naasta eelmiste hanke planeerimise sessioonide juurde ja jätkata sealt, kus pooleli jäin. | B2 |
| US-40 | Tehnilise spetsialistina tahan paluda AI-l koostada tehnilised spetsifikatsioonid konkreetse toote- või teenusekategooria jaoks, kasutades näiteid sarnastest edukatest hangetest. | B6 |

### Küsimustik: Vestlusliides

- **Q8.1** Kas eelistaksite samm-sammulist juhendatud töövoogu või vaba vestlust, kus saate küsida mida iganes?
- **Q8.2** Kui oluline on, et AI viitaks allikatele (konkreetsed hanked, regulatsioonid) oma vastustes?
- **Q8.3** Kas kasutaksite seda tööriista mobiilseadmetel või peamiselt lauaarvutil?
- **Q8.4** Kas AI peaks meeles pidama konteksti eelmistest hanke planeerimise sessioonidest?
- **Q8.5** Kas tahaksite jagada vestlust kolleegidega koostööpõhise hanke planeerimise jaoks?

---

## Prioriteedi hindamise juhend

Kasutage MoSCoW meetodit iga kasutajaloo hindamiseks:

| Hinnang | Tähendus |
|---------|----------|
| **Must** (Peab) | Kriitilise tähtsusega käivitamiseks — süsteem pole ilma selle funktsioonita kasutatav |
| **Should** (Peaks) | Oluline — tuleks lisada, kui vähegi võimalik |
| **Could** (Võiks) | Soovitav — lisada, kui aeg ja eelarve lubavad |
| **Won't** (Ei) | Praegu pole vaja — võib kaaluda tulevaste versioonide jaoks |

---

## Tagasiside esitamine

1. Vaadake läbi iga kasutajalugu ja määrake prioriteedihinnang (Must / Should / Could / Won't)
2. Vastake küsimustiku küsimustele oma reaalse kogemuse põhjal
3. Lisage märkused või kommentaarid kasutajalugudele, mis vajavad täpsustamist
4. Märgige puuduvad kasutajalood või funktsioonid, mida ei ole kaetud
5. Tagastage täidetud dokument Tendly tootemeeskonnale

---

*Tendly ostja AI tööriistad — kasutajalood ja küsimustik v1.0*
