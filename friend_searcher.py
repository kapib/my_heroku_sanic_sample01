# coding=utf-8
# coding=utf-8
from sanic.response import text
from sanic import Sanic
from sanic import response
import jinja2_sanic
import jinja2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import networkx as nx
import asyncio
from sample_service_api_client import SampleServiceApiClient


client = SampleServiceApiClient()
app = Sanic("sanic_jinja2_render")

template="<html><head></head><body><h2><font color=#ff4500>{{user_id}} {{searcher_name}}</font></h2>" \
         "<h3>{{friends_names}}</h3><div><img src='{{graph}}'> </div></body></html>"
jinja2_sanic.setup(
    app,
    loader=jinja2.DictLoader(
        {
            "templates.jinja2": template
        }
    )
)

@app.route("/")
async def func(request):
    return response.html("# /user/{nth}/{user_id} で{user_id}の{nth}次までの友達を表示"
                "<br><br> 例: /2/3 でid=3の友達の友達を表示."
                "<br>例: /4/8 でid=8の4次の友達(友達の友達の友達の友達)までを表示."
                "<br><br><br>#  /user/all ですべての人の関係を表示"
                )

def draw_network(client):
    img = io.BytesIO()
    G = nx.DiGraph()
    if len(client.friend_list) == 0 and not client.is_invalid_id:
        print("no friends")
        return "no friends"
    if client.is_invalid_id:
        return "invalid id"

    G.add_node(client.friend_searcher)
    G.add_nodes_from(client.friend_list)
    G.add_edges_from(client.friend_edges)
    pos = nx.spring_layout(G, k=3)
    nx.draw_networkx_edges(G, pos, node_color='b', alpha=0.6)
    nx.draw_networkx_nodes(G, pos, alpha=0.8, node_shape="o", nodelist=[int(client.friend_searcher)], node_color="r",
                           node_size=600)
    nx.draw_networkx_nodes(G, pos, alpha=0.6, node_shape="o", nodelist=client.friend_list, node_color="b", node_size=400)
    nx.draw_networkx_labels(G, pos, labels=client.node_name_list)
    nx.draw_networkx_labels(G, pos, labels={
        int(client.friend_searcher): str(client.friend_searcher) + ":" + client.friend_searcher_name})
    plt.axis('off')
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)

    plot_url = base64.b64encode(img.getvalue()).decode()
    graph = 'data:image/png;base64,{}'.format(plot_url)
    return graph

def draw_all_network(client):
    img = io.BytesIO()
    G = nx.DiGraph()

    G.add_nodes_from(client.friend_list)
    G.add_edges_from(client.friend_edges)
    pos = nx.circular_layout(G)
    nx.draw_networkx(G, pos, with_labels=False, alpha=0.5, node_size=800)
    nx.draw_networkx_edges(G, pos, width=1, alpha=0.8)
    nx.draw_networkx_labels(G, pos, labels=client.node_name_list)

    plt.axis('off')
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)

    plot_url = base64.b64encode(img.getvalue()).decode()
    graph = 'data:image/png;base64,{}'.format(plot_url)
    return graph

@app.route('/user/all')
@jinja2_sanic.template("templates.jinja2")
async def all_users(request):
    client.clear_data()
    await client.get_all_users_info([i for i in range(1, 11)])
    # await wait_for_task_finished()
    graph = draw_all_network(client)
    return {
        "searcher_name": "all network",
        "graph": graph,
    }

@app.route('/test')
@jinja2_sanic.template("templates.jinja2")
async def test(request):
    client.clear_data()
    results = await client.fetch_users_info_by_id_list([1, 2, 3, 4])
    for r in results:
        print(r)

@app.route('/test2/<nth>/<id>')
@jinja2_sanic.template("templates.jinja2")
async def test2(request, id, nth):
    client.clear_data()
    await client.get_nth_degree_friends_by_id_list([int(id)], int(nth))
    print("hogeeeeeeee")

@app.route('/user/<nth>/<number>')
@jinja2_sanic.template("templates.jinja2")
async def show_user_network(request, nth, number):
    client.clear_data()
    await client.get_nth_degree_friends_by_id_list([number], int(nth))

    graph = draw_network(client)
    if graph == "no friends":
        return text("No Friends!")
    elif graph == "invalid id":
        return text("invalid id")
    else:
        names = ""
        for v in client.node_name_list.values():
            names += v + "<br>"
        return {
            "searcher_name": ": "+client.friend_searcher_name,
            "friends_names": names,
            "user_id": number,
            "graph": graph,
        }


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    app.run(host="127.0.0.1", port=8000, debug=True)
    try:
        loop.run_forever()
    except:
        loop.stop()
