import matplotlib.pyplot as plt


class ReadTriplets:
    """Reading data and converting it to dictionary representation."""
    def __init__(self, filename):
        """Initialization of internal fields."""
        # dictionary: {user_j: {song_i: quantity_i} }
        # for each user we have a dictionary - the songs and quantity - how much times it was listened by this user
        # self.triplets = []
        self.triplets = {}
        self.min_rate = 0
        self.max_rate = 0
        self.read_file(filename)

    def read_file(self, filename):
        """Performs data reading and converting it to dictionary representation."""
        with open(filename) as f:
            previous_user = f.readline().split()[0]
            f.seek(0)
            previous_songs_dict = {}
            min_s = 10000
            max_s = 1
            for line in f.readlines():
                u_s_l = line.split()
                number = int(u_s_l[2])                  # quantity of listening
                if not int(u_s_l[0], 16) % 10:          # the proportional sampling
                    if previous_user != u_s_l[0]:       # filing the dictionary
                        if previous_songs_dict:
                            self.triplets[previous_user] = previous_songs_dict
                        previous_songs_dict = {}
                        previous_songs_dict[u_s_l[1]] = number
                        if number > max_s: max_s = number
                        if number < min_s: min_s = number
                        previous_user = u_s_l[0]
                    else:
                        if number > max_s: max_s = number
                        if number < min_s: min_s = number
                        previous_songs_dict[u_s_l[1]] = number
            if previous_songs_dict: # fill the last block
                self.triplets[previous_user] = previous_songs_dict
            self.max_rate = max_s
            self.min_rate = min_s


class HistogramDataExtractor:
    """Data extractor and histogram plots builder."""
    COLOR = (0.7, 0.8, 1.0)
    LINE_STYLE = '-'
    LABEL_SIZE = 14
    MARKER_SIZE = 8
    LINE_WIDTH = 1.5

    def __init__(self, tripl_dict, max_n):
        self.intervals = range(1, max_n + 1)
        self.tripl_dict = tripl_dict
        self.data = []
        self.fig_num = 1
        inter_len = len(self.intervals) - 1
        #self.count_data_by_number(tripl_dict)
        #self.count_data_by_user(tripl_dict)

    def count_data_by_user(self):
        """If user has {song1:1, song2:1, song3:1, song4:5, song5:5, song6:1} it means that our data is filled with
        [1, 5, 6] by this user
        """
        self.data = [number for number in self.intervals for key in self.tripl_dict if number in self.tripl_dict[key].values()]
            # for key in tripl_dict:
            #     if number in tripl_dict[key].values():
            #         self.data.append(number)
            #     # at least one song that user tried has been listed
                # (self.intervals[i]<= TIMES < self.intervals[i + 1]) times

    def count_data_by_number(self):
        """If user has {song1:1, song2:1, song3:1, song4:5, song5:5, song6:1} it means that our histogram data is filled with
        [1, 1, 1, 5, 5, 6] by this user
        """
        for number in self.intervals:
            for key in self.tripl_dict:
                self.data.extend([elem for elem in self.tripl_dict[key].values() if elem == number])

    def plot_figure(self, slices_number_in_gistogram, title):
        """Just plotting the histogram."""

        plt.figure(self.fig_num)
        plt.xlabel('Slices $x$', fontsize=self.LABEL_SIZE)
        plt.ylabel('Number of plays $y$', fontsize=self.LABEL_SIZE)
        # set size of the numbers on OX, OY, axes
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        plt.title(title)
        # makes limits showing OX axis equal to the given data
        #plt.xlim(x_nodes[0], x_nodes[-1])
        # plot original nodes from which interpolation model was built
        #plt.hist(self.intervals[0:-1], self.gisto_y, 'bo', label='points', markersize=self.MARKER_SIZE)
        plt.hist(self.data, slices_number_in_gistogram)
        # plot the grid
        plt.grid(color=self.COLOR, linestyle=self.LINE_STYLE)
        self.fig_num += 1




read_triplets = ReadTriplets('kaggle_visible_evaluation_triplets.txt')
gisto_extractor = HistogramDataExtractor(read_triplets.triplets, read_triplets.max_rate)
gisto_extractor.count_data_by_user()
gisto_extractor.plot_figure(60, "Counted_by_user")
gisto_extractor.count_data_by_number()
gisto_extractor.plot_figure(60, "Counted_by_number")
plt.show()
