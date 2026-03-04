import pandas as pd
import networkx as nx
from pyvis.network import Network
import time

print("--- GÉNÉRATION DU GRAPHE COMPLET + PANNEAU 100% DÉROULANT ---")

# ==========================================
# 1. CHARGEMENT DES DONNÉES
# ==========================================
df_ingr = pd.read_csv("ingr_info.tsv", sep='\t')
df_backbone = pd.read_csv("backbone.csv")

# ==========================================
# 2. CONSTRUCTION DU RÉSEAU
# ==========================================
G = nx.Graph()

for index, row in df_ingr.iterrows():
    nom = row['ingredient name']
    categorie = row['category']
    G.add_node(nom, label=nom, group=categorie, title=f"Catégorie : {categorie}")

for index, row in df_backbone.iterrows():
    source = str(row['0'])
    cible = str(row['1'])
    poids = int(row['2'])
    texte_survol = f"Partagent {poids} molécules"
    G.add_edge(source, cible, weight=poids, value=poids, title=texte_survol)

# Nettoyage : On supprime les ingrédients qui n'ont aucun lien dans le backbone
G.remove_nodes_from(list(nx.isolates(G)))

# ==========================================
# 3. RÉCUPÉRATION DES LISTES POUR LE MENU
# ==========================================
# On récupère uniquement les ingrédients et catégories qui ont "survécu" dans le graphe !
ingredients_presents = sorted(list(G.nodes()))
categories_presentes = sorted(list(set(nx.get_node_attributes(G, 'group').values())))

# ==========================================
# 4. CRÉATION DE LA PAGE WEB
# ==========================================
net = Network(height="100vh", width="100%", bgcolor="#222222", font_color="white", select_menu=False, filter_menu=False)
net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=200)
net.from_nx(G)

fichier_sortie = "flavor_network_officiel.html"
net.save_graph(fichier_sortie)

# ==========================================
# 5. INJECTION DE NOTRE SUPER PANNEAU
# ==========================================

# Génération des options HTML pour les Catégories
options_cat = '<option value="all">Afficher TOUTES les catégories</option>'
for cat in categories_presentes:
    options_cat += f'<option value="{cat}">{cat.capitalize()}</option>'

# Génération des options HTML pour les Ingrédients
options_ingr = '<option value="">-- Choisissez un aliment --</option>'
for ingr in ingredients_presents:
    options_ingr += f'<option value="{ingr}">{ingr.capitalize()}</option>'

code_html_personnalise = f"""
<div style="position: absolute; top: 20px; right: 20px; width: 340px; max-height: 90vh; overflow-y: auto; z-index: 1000; background: rgba(30,30,30,0.95); padding: 20px; border-radius: 10px; color: white; font-family: sans-serif; border: 2px solid #555; box-shadow: 0px 4px 10px rgba(0,0,0,0.5);">
    
    <h3 style="margin-top: 0; color: #ff9800; border-bottom: 1px solid #555; padding-bottom: 5px;">1. Filtrer par Catégorie</h3>
    <select id="select-categorie" onchange="filtrerCategorie()" style="width: 100%; padding: 10px; border-radius: 5px; margin-bottom: 20px; font-weight: bold; cursor: pointer;">
        {options_cat}
    </select>

    <h3 style="margin-top: 0; color: #4CAF50; border-bottom: 1px solid #555; padding-bottom: 5px;">2. Isoler un Mariage</h3>
    
    <select id="ingr1" style="width: 100%; padding: 10px; border-radius: 5px; margin-bottom: 10px; cursor: pointer;">
        {options_ingr}
    </select>
    
    <select id="ingr2" style="width: 100%; padding: 10px; border-radius: 5px; margin-bottom: 15px; cursor: pointer;">
        {options_ingr}
    </select>
    
    <div style="display: flex; gap: 10px; margin-bottom: 10px;">
        <button onclick="chercherLien()" style="padding: 10px; flex: 1; cursor: pointer; background: #4CAF50; color: white; border: none; border-radius: 5px; font-weight: bold;">Analyser</button>
    </div>
    
    <div id="result-msg" style="margin-bottom: 15px; font-weight: bold; font-size: 14px; text-align: center;"></div>

    <button onclick="resetGraphe()" style="padding: 12px; width: 100%; cursor: pointer; background: #f44336; color: white; border: none; border-radius: 5px; font-weight: bold; font-size: 16px;">Réinitialiser le Graphe</button>
</div>

<script>
// Fonction pour le Face-à-Face
function chercherLien() {{
    var n1 = document.getElementById('ingr1').value;
    var n2 = document.getElementById('ingr2').value;
    var msg = document.getElementById('result-msg');
    
    // On remet la catégorie sur "Toutes"
    document.getElementById('select-categorie').value = 'all';
    
    if(!n1 || !n2) {{
        msg.innerHTML = "Veuillez sélectionner deux aliments dans les listes.";
        return;
    }}
    
    var allNodes = nodes.get();
    var id1 = null; var id2 = null;
    
    for(var i=0; i<allNodes.length; i++) {{
        if(allNodes[i].label === n1) id1 = allNodes[i].id;
        if(allNodes[i].label === n2) id2 = allNodes[i].id;
    }}
    
    var allEdges = edges.get();
    var foundEdge = null;
    for(var i=0; i<allEdges.length; i++) {{
        var e = allEdges[i];
        if((e.from === id1 && e.to === id2) || (e.from === id2 && e.to === id1)) {{
            foundEdge = e; break;
        }}
    }}
    
    // Cacher tout sauf les 2 aliments
    var nodeUpdates = [];
    for(var i=0; i<allNodes.length; i++) {{
        nodeUpdates.push({{id: allNodes[i].id, hidden: (allNodes[i].id !== id1 && allNodes[i].id !== id2)}});
    }}
    nodes.update(nodeUpdates);
    
    var edgeUpdates = [];
    for(var i=0; i<allEdges.length; i++) {{
        edgeUpdates.push({{id: allEdges[i].id, hidden: (!foundEdge || allEdges[i].id !== foundEdge.id)}});
    }}
    edges.update(edgeUpdates);

    network.fit({{nodes: [id1, id2], animation: true}});

    if(foundEdge) {{
        msg.innerHTML = "Mariage Validé !<br><br><span style='color:#4CAF50; font-size:24px;'>" + foundEdge.value + "</span><br>molécules partagées";
    }} else {{
        msg.innerHTML = "Aucun lien direct exceptionnel entre ces deux aliments.";
    }}
}}

// Fonction pour le filtre par catégorie
function filtrerCategorie() {{
    var cat = document.getElementById('select-categorie').value;
    document.getElementById('result-msg').innerHTML = '';
    
    var allNodes = nodes.get();
    var nodeUpdates = [];
    var visibleNodes = new Set();
    
    for(var i=0; i<allNodes.length; i++) {{
        if(cat === 'all' || allNodes[i].group === cat) {{
            nodeUpdates.push({{id: allNodes[i].id, hidden: false}});
            visibleNodes.add(allNodes[i].id);
        }} else {{
            nodeUpdates.push({{id: allNodes[i].id, hidden: true}});
        }}
    }}
    nodes.update(nodeUpdates);
    
    var allEdges = edges.get();
    var edgeUpdates = [];
    for(var i=0; i<allEdges.length; i++) {{
        if(visibleNodes.has(allEdges[i].from) && visibleNodes.has(allEdges[i].to)) {{
            edgeUpdates.push({{id: allEdges[i].id, hidden: false}});
        }} else {{
            edgeUpdates.push({{id: allEdges[i].id, hidden: true}});
        }}
    }}
    edges.update(edgeUpdates);
    network.fit({{animation: true}});
}}

// Fonction Reset
function resetGraphe() {{
    document.getElementById('select-categorie').value = 'all';
    document.getElementById('ingr1').value = '';
    document.getElementById('ingr2').value = '';
    document.getElementById('result-msg').innerHTML = '';
    
    var nodeUpdates = nodes.get().map(n => ({{id: n.id, hidden: false}}));
    nodes.update(nodeUpdates);
    
    var edgeUpdates = edges.get().map(e => ({{id: e.id, hidden: false}}));
    edges.update(edgeUpdates);
    
    network.fit({{animation: true}});
}}
</script>
"""

with open(fichier_sortie, "a", encoding="utf-8") as file:
    file.write(code_html_personnalise)

print("TERMINÉ ! Lance le fichier HTML. Des menus déroulants propres t'attendent !")