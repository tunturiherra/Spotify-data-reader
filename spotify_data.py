import json
import datetime


# muunnetaan tällä funktiolla Spotifylta tuleva aikaleima helpommin luettavaan muotoon
def get_year(timestamp):
    date_object = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    return date_object.year


while True:
    try:
        # Jos Windowsilla yrittää kopioida tiedoston sijaintia, niin tulee lainausmerkit mukaan.
        # Käytetään replacea, jotta käyttäjän ei tarvitse erikseen siivota inputista lainausmerkkejä,
        # vaan sen tekee ohjelma itse. Tällöin käyttö on jouhevampaa!
        # Tähän täytyy toki miettiä toinen toteutustapa, ehkä kysytään kansiota?
        filepath = input("Anna tiedoston sijainti: \n").replace('"', "")

        # haetaan tiedot json-tiedostosta ja lisätään se omaksi muuttujaksi
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
        try:
            # kysytään käyttäjältä haluttua vuotta
            listen_year = int(input("Anna haluttu vuosi, jonka perusteella haetaan striimatut laulut "
                                    "(Luku 0 tulostaa kaikki vuodesta riippumatta.):\n").strip())

            # jotta ohjelma ei tulostaisi miljoonaa kertaa virheviestiä, otetaan vain toteutuneet arvot.
            found_songs = False

            for song in data:
                # tarkistetaan ja tulostetaan tiedot vain, jos vuosi täsmää
                if get_year(song["ts"]) == listen_year or listen_year == 0:
                    found_songs = True
                    artist = song["master_metadata_album_artist_name"]
                    track = song["master_metadata_track_name"]
                    year = get_year(song["ts"])
                    device = song["platform"]
                    # tulostetaan yhdelle riville per dictionary
                    print(f"{artist}: {track}, kuunneltu vuonna {year} laitteelta {device}\n")

            if not found_songs:
                print(f"Vuodelta {listen_year} ei löytynyt hakutuloksia.")

            restart = input("Haluatko hakea toisesta tiedostosta tietoja? (k/e):\n").lower().strip()
            if restart == "k":
                continue
            else:
                print("Näkemiin!")
            break
            
        # jos käyttäjä ei syötä mitään.
        except ValueError:
            print("Et syöttänyt lukua.\n")

    # ilmoitetaan käyttäjälle, että tiedoston polku oli väärä.
    except FileNotFoundError:
        print("Tiedostoa ei löydy. Onhan polku varmasti oikein?")

    restart = input("Haluatko yrittää uudelleen? (k/e):\n").lower().strip()
    if restart == "k":
        continue
    else:
        print("Näkemiin!")
    break
