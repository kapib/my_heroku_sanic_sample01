# coding=utf-8
import aiohttp
import asyncio


class SampleServiceApiClient:
    def __init__(self):
        self.base_url = "https://freundschaft.herokuapp.com/user/"
        self.users_info = []
        self.new_friend_list = []
        self.friend_list = []
        self.rec = 0
        self.friend_searcher = None
        self.friend_searcher_name = ''
        self.node_name_list = {}
        self.friend_edges = []
        self.is_invalid_id = False

    def clear_data(self):
        self.users_info = []
        self.friend_list = []
        self.new_friend_list = []
        self.rec = 0
        self.friend_searcher = None
        self.friend_searcher_name = ''
        self.node_name_list = {}
        self.friend_edges = []
        self.is_invalid_id = False

    async def get_nth_degree_friends_by_id_list(self, user_id_list, nth=2):
        '''
        nthは友達の次数
        :param user_id_list:
        :param nth:
        :return:
        '''
        if self.friend_searcher is None:
            self.friend_searcher = user_id_list[0]
        self.rec = int(nth)
        for i in range(nth):
            results = await self.fetch_users_info_by_id_list(user_id_list)
        # ここでstore users friend したらいい
            print(results)
            if (i == 0) and len(results) == 1 and (not 'friends' in results[0].keys()):
                self.is_invalid_id = True
                return
            user_id_list = self.store_users_friends(results)
            if user_id_list == []:
                break
        # 最後の階層の友達だけ名前がないので、取得する必要があるが、必要なものに絞るとさらに効率良い
        unknown_name_id_list = self.unknown_name_in_new_friend_list() #最後の名前リストで現在の名前リストに乗っていないものをチョイス
        results = await self.fetch_users_info_by_id_list(unknown_name_id_list)
        self.store_users_name(results)
        # 自分自身がnode listにいたら除く
        self.remove_friend_searcher_from_node_name_list()
        print(self.new_friend_list)
        print(self.friend_list)
        print(self.node_name_list)


    def remove_friend_searcher_from_node_name_list(self):
        keys = [k for k in self.node_name_list.keys()]
        if int(self.friend_searcher) in keys:
            self.node_name_list.pop(int(self.friend_searcher))
        print(self.node_name_list)

    def unknown_name_in_new_friend_list(self):
        ret = []
        known_name_id = [key for key in self.node_name_list.keys()]
        for id_ in self.new_friend_list:
            if not id_ in known_name_id:
                ret.append(id_)
        return ret

    def store_users_friends(self, results):
        if results == []:
            return []
        self.new_friend_list = []

        for info in results:
            if 'friends' in info.keys():
                # 友達リストを取得する
                self.new_friend_list += info['friends']
                # ネットワーク図を描くために友達のつながりのタプルを取得
                for f in info['friends']:
                    self.friend_edges.append((info['id'], f))
                # ここで名前も取得することにする
                self.node_name_list.update({info['id']: str(info['id'])+":"+info['name']})
                # 一番元のuserの名前を記録する
                if self.friend_searcher is not None:
                    if int(info['id']) == int(self.friend_searcher):
                        self.friend_searcher_name = info['name']
            else:
                print("maybe invalid ID.")
                return

        # すべての友達リストに追加する
        self.friend_list += self.new_friend_list
        # 重複を除く
        self.friend_list = list(set(self.friend_list))
        # 重複を除く
        self.new_friend_list = list(set(self.new_friend_list))
        self.friend_list.sort() # これは最後でもいいかも
        # 自分自身が友達リストにいたら除く
        if self.friend_searcher is not None:
            if int(self.friend_searcher) in self.new_friend_list:
                self.new_friend_list.remove(int(self.friend_searcher))
            if int(self.friend_searcher) in self.friend_list:
                self.friend_list.remove(int(self.friend_searcher))
        # 友達のつながりの重複を除く
        self.friend_edges = list(set(self.friend_edges))

        return self.new_friend_list


    def store_users_name(self, results):
        # もうすでにいるときは探しに行く必要ない
        for info in results:
            if 'name' in info.keys():
                self.node_name_list.update({info['id']: str(info['id'])+":"+info['name']})
            else:
                # print("User ID {} could be invalid.".format(info['id']))
                self.node_name_list.update({info['id']: str(info['id'])+":"+""})

    async def get_all_users_info(self, user_id_list):
        '''
        nthは友達の次数
        :param user_id_list:
        :param nth:
        :return:
        '''
        results = await self.fetch_users_info_by_id_list(user_id_list)
        # ここでstore users friend したらいい
        self.store_users_friends(results)

    async def fetch_user_info_by_id(self, user_id):
        async with aiohttp.ClientSession() as session:
            url = self.base_url + str(user_id)
            print(url)
            async with session.get(url) as response:
                return await response.json()

    async def fetch_users_info_by_id_list(self, user_id_list):
        coroutines = []
        if user_id_list == []:
            return []
        for id_ in user_id_list:
            coroutines.append(self.fetch_user_info_by_id(id_))
        results = await asyncio.gather(*coroutines)
        return results

    def store_users_info(self, future):
        for result in future.result():
            self.users_info.append(result)
        print(self.users_info)