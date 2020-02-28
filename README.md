# Kassenprogramm für Mosterei

Dieses Kassenprogramm ist seit mehreren Jahren in unserer Lohnmosterei/Lohnkelterei im Einsatz und berechnet Preise, verwaltet Kunden und wickelt die Bar- und EC-Zahlungen ab.

Die Kassierfunktion wurde für innerbetriebliche Anwendung entwickelt und ist **NICHT** geprüft auf Einhaltung der GDPdU.

Dieses Programm wird hier veröffentlicht ohne Gewährleistung, ohne Anspruch auf Rechtsgültigkeit, Vollständigkeit oder Erfüllung irgend eines Zwecks.

Eine TSE (Swissbit) kann benutzt werden. DSFinV-K-Export ist bisher nicht implementiert, die Daten sollten aber ausreichend zur Verfügung stehen.

## Ausblick

Die Kasse soll rechtlichen Anforderungen Rechnung tragen. Langfristig ist eine stärkere Modularisierung geplant, um Einzelteile portable nutzen zu können. 

Die Planung ist, die Speicherung und GUI voneinander zu trennen in verschiedene Prozesse, auch über Netzwerk ansprechbar um von mehreren Clients Daten beisteuern zu können. Dafür soll eine JSON-REST-API entwickelt werden.

## Lizenz

Sofern fremder Sourcecode hier im Repository enthalten ist (Bootstrap, JQuery-UI, FontAwesome, ...) gilt natürlich die entsprechende Lizenz.

Der sonstige enthaltene Code ist meine eigene Entwicklung und freigegeben unter CC-Zero, also "Public Domain". Mitarbeit, auch bei der Loslösung der Komponenten in eigene Module, wird gern gesehen.

Der Code zur Unterstützung der TSE-Einheit ist separat verfügbar unter https://github.com/bwurst/python-tse. Vielen Dank an Leon Fellows von der fairtragen GmbH, der mir ein Entwickler-TSE-Sample zur Verfügung gestellt hat.
