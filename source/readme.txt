Alapötlet: Egyszerű folyadékszimulátor, ami kezeli a tartályok hő- és nyomásváltozását
	
Alapelemek:
	* Tartály, cső, szelep
	
	* A rendszer egy diszkrét idejű esemény modell.
	* Ha A(t) a rendszer állapota a t. pillanatban, akkor A(t+1) = f(A(t), B(t)), ahol f a rendszer függvénye, B(t) pedig a t. időpillanatban a beavatkozás.
	* Egy időlépés feladatai:
		* Kiszámolni, hogy a csövek elején és végén mennyi a nyomás
		* A nyomáskülönbség és dt alapján kiszámolni, hogy mennyi folyadék lép be és merre.
		* A kiinduló oldalból ezt ki kell vonni, a túloldalra hozzá kell adni
	      * A tárolókban lévő folyadékobjektumnak képesnek kell lennie a kivonást és a hozzáadást (és az ezzel járó hőmérsékletváltozást) kezelni.

Tartály:
	Tároló.
	Tárolja, hogy melyik csővezeték milyen magasságban csatlakozik bele
	Leírja:
		* maximum folyadékmennyiség
		* egy függvény, ami megadja, hogy adott folyadékmennyiség mellett adott ponton mekkora a nyomás
	Állapotváltozók:
		* Aktuális folyadékmennyiség
		* Aktuális hőmérséklet
		
	
Cső:
	Tároló
	Tárolókat köt össze.
	Leírja:
		* A tároló
		* B tároló
		* Hossz
		* Nyomáscsökkenést leíró függvény
	Állapotváltozók
		* Egy csőnek nincs állapota. Ha modellezni szeretnénk azt, hogy egy cső folyadékot tárol, akkor azt egy plusz tartállyal lehet megtenni
		
Szelep:
	Tároló
	A keresztmetszetét változtatni képes, nulla kapacitású cső.
	
Folyadék
	Kezeli a tárolókban lévő folyadék mennyiségét és hőmérsékletét
	Leírja:
		* Hőmérséklet
		* Mennyiség
		(* Összetétel)
		(	* Hőkapacitás)
	Metódusok
		* remove : Kivesz egy adagot. Ez a hőmérsékletet nem, de a mennyiséget befolyásolja.
					  Visszaad egy folyadékobjektumot a kért mennyiséggel, ha kielégíthető, egyébként a legnagyobbal, ami megoldható
		* add    : Hozzáad egy adott folyadékobjektumot. Változtatja a mennyiséget (növeli) és a hőmérsékletet (kiegyenlíti)
