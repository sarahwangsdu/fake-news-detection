from utils.ArticlesHandler import ArticlesHandler
from utils import solve, embedding_matrix_2_kNN, get_rate, accuracy, precision, recall, f1_score
from utils.Trainer_graph import TrainerGraph
from utils import Config, accuracy_sentence_based
import time
import numpy as np
# from utils.postprocessing.SelectLabelsPostprocessor import SelectLabelsPostprocessor
from utils.Trainer_graph import TrainerGraph
from sklearn import svm
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

config = Config('config/')

print("start....")


all_accuracys = []


count = 0
for repeat in range(config.stats.iteration_stat):
    debut = time.time()

    count += 1
    print(str(repeat) + ", " + str(count))
    start_time = time.time()


    handler = ArticlesHandler(config)



    # Save in a pickle file. To open, use the pickle dataloader.
    #handler.articles.save("../Dataset/train_fake.pkl")
    # Only recompute labels:
    # handler.articles.compute_labels()

    C = handler.get_tensor()
    # select_labels = SelectLabelsPostprocessor(config, handler.articles)
    # handler.add_postprocessing(select_labels, "label-selection")
    # handler.postprocess()
    labels = np.array(handler.articles.labels)
    all_labels = np.array(handler.articles.labels_untouched)

    print(labels,all_labels)

    if config.learning.method_learning == "FaBP":
        assert max(labels) == 2, "FaBP can only be used for binary classification."

    print(len(all_labels), "Articles")

    if config.graph.node_features == config.embedding.method_decomposition_embedding:
        C_nodes = C.copy()
    else:
        config.embedding.set("method_decomposition_embedding", config.graph.method_create_graph)
        C_nodes = handler.get_tensor()

    fin = time.time()
    print("get tensor and decomposition done", fin - debut)
    sentence_to_articles = None if not config.graph.sentence_based else handler.articles.sentence_to_article
    graph = embedding_matrix_2_kNN(C, k=config.graph.num_nearest_neighbours,
                                   sentence_to_articles=sentence_to_articles).toarray()
    fin3 = time.time()
    print("KNN done", fin3 - fin)

    if config.learning.method_learning == "FaBP":
        # classe  b(i){> 0, < 0} means i ∈ {“+”, “-”}
        beliefs = solve(graph, labels[:])
        fin4 = time.time()
        print("FaBP done", fin4 - fin3)
    elif config.learning.method_learning in ["SVM", "RF"]:
        training_mask = labels > 0
        test_mask = labels == 0
        training_set = C[training_mask, :]
        l = labels[training_mask]
        l[l == 2] = -1
        print("Fitting")
        if config.learning.method_learning == "SVM":
            clf = svm.SVC(gamma='scale')
        else:  # Random forest
            clf = RandomForestClassifier(n_estimators=100, max_depth=2, random_state=0)
        clf.fit(training_set, l)
        beliefs = labels
        beliefs[test_mask] = clf.predict(C[test_mask, :])
        beliefs[beliefs == -1] = 2
    else:
        trainer = TrainerGraph(C_nodes, graph, all_labels, labels)
        beliefs, acc_test = trainer.train()
        print(acc_test)
        fin4 = time.time()
        print("Learning done", fin4 - fin3)
        # Compute hit rate
        # TODO: changer pour le multiclasse...
        #beliefs[beliefs >= 0] = 1
        #beliefs[beliefs < 0] = 2


    if config.graph.sentence_based:
        acc = accuracy_sentence_based(handler, beliefs)
    else:
        #print(all_labels, beliefs)
        acc = accuracy_score(all_labels, beliefs)

    #print("Accuracy", acc)

    all_accuracys.append(acc)
    end_time = time.time()
    print(end_time - start_time)

print(np.mean(all_accuracys))
print(np.std(all_accuracys))

print("end.....")

np.save("/media/"+str(config.embedding.method_decomposition_embedding)+"_mean"+str(config.graph.num_nearest_neighbours)+ str(config.stats.ratio_labeled)+".npy", np.mean(all_accuracys))
np.save("/media/"+str(config.embedding.method_decomposition_embedding)+"_std"+str(config.graph.num_nearest_neighbours)+str(config.stats.ratio_labeled)+".npy", np.std(all_accuracys))
