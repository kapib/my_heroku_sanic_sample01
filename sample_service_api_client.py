# coding=utf-8
import aiohttp
import asyncio


class SampleServiceApiClient:
    def __init__(self):
        self.base_url = "https://freundschaft.herokuapp.com/user/"
        self.users_info = []
        self.friend_list = []
        self.rec = 0
        self.friend_searcher = None
        self.friend_searcher_name = ''
        self.node_name_list = {}
        self.friend_edges = []
        self.is_completed = False
        self.is_invalid_id = False

    def clear_data(self):
        self.users_info = []
        self.friend_list = []
        self.rec = 0
        self.friend_searcher = None
        self.friend_searcher_name = ''
        self.node_name_list = {}
        self.friend_edges = []
        self.is_completed = False
        self.is_invalid_id = False

    async def fetch_user_info_by_id(self, user_id):
        async with aiohttp.ClientSession() as session:
            url = self.base_url + str(user_id)
            print(url)
            async with session.get(url) as response:
                return await response.json()

    def fetch_users_info_by_id_list(self, user_id_list, callback=None):
        self.users_info = []
        coroutines = []
        for id_ in user_id_list:
            coroutines.append(self.fetch_user_info_by_id(id_))
        future = asyncio.gather(*coroutines)
        asyncio.ensure_future(future)
        if callback is not None:
            future.add_done_callback(callback)

    def store_users_info(self, future):
        for result in future.result():
            self.users_info.append(result)
        print(self.users_info)

    def fetch_users_name_by_id_list(self, user_id_list):
        self.fetch_users_info_by_id_list(user_id_list, self.store_users_name)

    def store_users_name(self, future):
        name_list = []
        for info in future.result():
            if 'name' in info.keys():
                name_list.append(info['name'])
                self.node_name_list.update({info['id']: str(info['id'])+":"+info['name']})
            else:
                # print("User ID {} could be invalid.".format(info['id']))
                name_list.append("")
        print(self.node_name_list)
        self.is_completed = True

    def fetch_users_friends_by_id_list(self, user_id_list):
        self.fetch_users_info_by_id_list(user_id_list, self.store_users_friends)

    def store_users_friends(self, future):
        friends_list = []
        # print(future.result())

        for info in future.result():
            if 'friends' in info.keys():
                # 友達リストを取得する
                friends_list += info['friends']
                # 一番元のuserの名前を記録する
                if int(info['id']) == int(self.friend_searcher):
                    self.friend_searcher_name = info['name']
                # ネットワーク図を描くために友達のつながりのタプルを取得
                for f in info['friends']:
                    self.friend_edges.append((info['id'], f))
            else:
                print("maybe invalid ID.")
                self.is_completed = True
                self.is_invalid_id = True
                return

        self.friend_list += friends_list
        # 重複を除く
        self.friend_list = list(set(self.friend_list))
        # 再帰の回数
        self.rec -= 1

        # print("self.friend_list, friends_list:", self.friend_list, friends_list)
        # もし友達リストが空ならそこで終了
        if self.friend_list == []:
            self.is_completed = True
            return

        if self.rec != 0:
            self.get_nth_degree_friends_by_id_list(self.friend_list, self.rec)
        else:
            self.friend_list.sort()
            ret = self.friend_list.copy()
            # 自分自身が友達リストにいたら除く
            if int(self.friend_searcher) in self.friend_list:
                self.friend_list.remove(int(self.friend_searcher))
            self.fetch_users_name_by_id_list(self.friend_list)
            # print(self.friend_list)
            # 友達のつながりの重複を除く
            self.friend_edges = list(set(self.friend_edges))
            # print(self.friend_edges)
            return ret

    def get_nth_degree_friends_by_id_list(self, user_id_list, nth=2):
        '''
        nthは友達の次数
        :param user_id_list:
        :param nth:
        :return:
        '''
        if self.friend_searcher is None:
            self.friend_searcher = user_id_list[0]
        self.rec = int(nth)
        all_friends = self.fetch_users_friends_by_id_list(user_id_list)
        return all_friends


    def get_all_users_info(self):
        self.fetch_users_info_by_id_list([i for i in range(1, 11)], self.store_all_users_info)

    def store_all_users_info(self, future):
        for result in future.result():
            self.users_info.append(result)
        for d in self.users_info:
            id = d['id']
            name = d['name']
            friends = d['friends']
            self.node_name_list.update({id: str(id)+':'+name})
            for f in friends:
                self.friend_edges.append((id, f))
        self.friend_edges = list(set(self.friend_edges))
        self.is_completed = True
        # print(self.node_name_list)
        # print(self.friend_edges)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    client = SampleServiceApiClient()
    client.node_name_list = {}
    client.get_all_users_info()

    try:
        loop.run_forever()
    except:
        loop.stop()