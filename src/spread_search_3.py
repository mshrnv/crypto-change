"""Module to search spread"""
from datetime import datetime
from functools import reduce
import time
import redis
import networkx as nx
import matplotlib.pyplot as plt
from pymongo import MongoClient
from consts import chains


def get_timestamp():
    """Returns current timestamp"""
    return datetime.now()


def get_redis_data(redis_client: redis.Redis):
    """Returns all data from Redis"""
    data = {}
    keys = redis_client.keys('*')
    for key in keys:
        data[key] = redis_client.hgetall(key)

    return data


def prepare_currencies_data(currencies_data):
    """Transform currencies dict data to (c1, c1): [ask|bid]"""
    data = {}
    for ticker, values in currencies_data.items():
        # All currencies have 3-letter name
        if 'MX' in ticker:
            ccy1, ccy2 = ticker[:2], ticker[2:]
        else:
            ccy1, ccy2 = ticker[:3], ticker[3:]

        data[(ccy1, ccy2)] = 1 / float(values['bid'])
        data[(ccy2, ccy1)] = float(values['ask'])

    return data


def create_graph(prepared_data):
    """Creates multi di graph"""
    graph = nx.MultiDiGraph()

    for pair, value in prepared_data.items():
        ccy1, ccy2, = pair
        graph.add_edge(ccy1, ccy2, weight=value)

    return graph


def draw_graph(graph, weights_data):
    """Graph visualization"""
    pos = nx.circular_layout(graph)
    plt.figure(figsize=(10, 10))

    nx.draw(
        graph, pos, edge_color='black', width=1, linewidths=1,
        node_size=1600, node_color='pink', alpha=0.9,
        labels={node: node for node in graph.nodes()}
    )

    nx.draw_networkx_edge_labels(
        graph, pos,
        edge_labels=weights_data,
        font_color='red',
        verticalalignment='bottom'
    )

    plt.axis('off')
    plt.show()


def calc_chain_spread(crypto_chain):
    """Calculating spred of chain"""
    result = reduce(lambda x, y: x * y, crypto_chain)
    spread = result * 100 - 100
    return spread


def calc_all_chains_spread(weights, all_chains, mongo_collection):
    """Chains bruteforce for profitability and saving to MongoDB"""
    for chain in all_chains:
        chain_path = [
            weights[(chain[0], chain[1], 0)],
            weights[(chain[1], chain[2], 0)],
            weights[(chain[2], chain[3], 0)],
        ]

        mongo_collection.insert_one({
            "chain": " -> ".join(chain),
            "spread": round(calc_chain_spread(chain_path), 4),
            "timestamp": get_timestamp()
        })

        print('-----------------')
        print(" -> ".join(chain))
        print(*chain_path, sep=' -> ')
        print('Spread: ' + str(round(calc_chain_spread(chain_path), 4)) + '%')


if __name__ == '__main__':
    # Redis Connection
    client = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        charset="utf-8",
        decode_responses=True
    )

    # MongoDB Connection
    mongo_client = MongoClient(
        '127.0.0.1',
        27017,
    )

    db = mongo_client.crypto
    mongo_spreads = db.mexc_spreads_3

    # Every 10sec searching for profitability chains
    while True:
        currencies = get_redis_data(client)
        data = prepare_currencies_data(currencies)
        currencies_graph = create_graph(data)
        print(currencies_graph)

        attrs = nx.get_edge_attributes(currencies_graph, 'weight')
        calc_all_chains_spread(attrs, chains, mongo_spreads)

        time.sleep(10)
