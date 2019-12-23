# Kassenprogramm für Mosterei

Dieses Kassenprogramm ist seit mehreren Jahren in unserer Lohnmosterei/Lohnkelterei im Einsatz und berechnet Preise, verwaltet Kunden und wickelt die Bar- und EC-Zahlungen ab.

Die Kassierfunktion wurde für innerbetriebliche Anwendung entwickelt und ist **NICHT** geprüft auf Einhaltung der GDPdU.

Dieses Programm wird hier veröffentlicht ohne Gewährleistung, ohne Anspruch auf Rechtsgültigkeit, Vollständigkeit oder Erfüllung irgend eines Zwecks.

## Ausblick

Die Kasse soll künftigen rechtlichen Anforderungen Rechnung tragen und daher stärker modularisiert werden um Einzelteile portable nutzen zu können. Die Unterstützung von DSFinV-K und TSE ist geplant aber nicht umgesetzt.

Die Planung ist, die Speicherung und GUI voneinander zu trennen in verschiedene Prozesse, auch über Netzwerk ansprechbar um von mehreren Clients Daten beisteuern zu können. Dafür soll eine JSON-REST-API entwickelt werden.

## Lizenz

Sofern fremder Sourcecode hier im Repository enthalten ist (Bootstrap, JQuery-UI, FontAwesome, ...) gilt natürlich die entsprechende Lizenz.

Der sonstige enthaltene Code ist meine eigene Entwicklung und freigegeben unter CC-Zero, also "Public Domain". Mitarbeit, auch bei der Loslösung der Komponenten in eigene Module, wird gern gesehen.

