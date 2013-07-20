from action import Action
import logging


class CleanModules(Action):
    def run(self):
        logging.info("Removing fetched modules..")
        remove_list = [m for m in self.modules_pool if m.source in ["svn", "git"] and m.isfetched]
        remove_list.reverse()  # we will remove modules in backward order
        if len(remove_list):
            for m in remove_list:
                print("\t" + m.url + " [from: " + m.path + "]")
                m.remove_dir_from_disk()
        else:
            logging.info("There are no modules to be removed")