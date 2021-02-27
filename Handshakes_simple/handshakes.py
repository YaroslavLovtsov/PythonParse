import database
import os
from dotenv import load_dotenv

DEFAULT_FRIENDS_DICTIONARY = {'ivanov': ['kuznecov', 'sergeev', 'dmitriev'],
                              'petrov': ['sidorov', 'dmitriev'],
                              'sidorov': ['andreev', 'petrov', 'smirnov'],
                              'kuznecov': ['ivanov'],
                              'sergeev': ['ivanov'],
                              'dmitriev': ['ivanov', 'petrov'],
                              'andreev': ['sidorov'],
                              'smirnov': ['sidorov']}


class FindHandshake:
    def __init__(self, start_side, end_side):
        self.start_side = start_side
        self.end_side = end_side

        load_dotenv('.env')

        self.friends_chains_db = database.Database(os.getenv("SQLDB_URL"))
        self.from_end = False
        self.current_check_list = [start_side]
        self.current_target_list = [end_side]
        self.success_achieved = False
        self.fail_not_achieved = True
        self.result_chain = ''

        add_data_start = {
            'user': start_side,
            'from_end': False,
            'chain': start_side
        }
        self.friends_chains_db.create_user_data(add_data_start)

        add_data_end = {
            'user': end_side,
            'from_end': True,
            'chain': end_side
        }
        self.friends_chains_db.create_user_data(add_data_end)

    @staticmethod
    def get_friends_list(current_side):
        return DEFAULT_FRIENDS_DICTIONARY[current_side]

    def get_new_layer(self):
        new_target_list = []

        for cur_side_el in self.current_check_list:
            current_friends_list = self.get_friends_list(cur_side_el)
            current_side_data = self.friends_chains_db.get_user_data(cur_side_el)

            for current_friend in current_friends_list:
                current_friend_data = self.friends_chains_db.get_user_data(current_friend)

                if current_friend in self.current_target_list:
                    self.success_achieved = True
                    if self.from_end:
                        self.result_chain = f'->'
                        self.result_chain = f'{current_friend_data.chain}->{current_side_data.chain}'
                        pass
                    else:
                        self.result_chain = f'{current_side_data.chain}->{current_friend_data.chain}'
                        pass

                elif not current_friend_data:
                    new_target_list.append(current_friend)
                    if current_side_data.from_end:
                        add_data = {
                            'user': current_friend,
                            'from_end': True,
                            'chain': f'{current_side_data.chain}->{current_friend}'
                        }
                    else:
                        add_data = {
                            'user': current_friend,
                            'from_end': False,
                            'chain': f'{current_friend}->{current_side_data.chain}'
                        }
                    self.friends_chains_db.create_user_data(add_data)

        if len(new_target_list) == 0:
            self.fail_not_achieved = False
            if not self.success_achieved:
                print(f'Рукопожатий между {self.start_side} и {self.end_side} не обнаружено.')
        else:
            self.current_check_list = self.current_target_list.copy()
            self.current_target_list = new_target_list.copy()
            self.from_end = not self.from_end

    def construct_chain(self):
        while not self.success_achieved and self.fail_not_achieved:
            self.get_new_layer()

        if self.success_achieved:
            print(self.result_chain.replace('->->', '->'))

FindHandshake('ivanov', 'sidorov').construct_chain()
