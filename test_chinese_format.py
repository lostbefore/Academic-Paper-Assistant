"""
测试中文论文格式
"""
from pathlib import Path
from backend.docx_generator import DocxGenerator

# 示例中文论文内容
sections = {
    'title': '基于深度学习的自然语言处理研究进展',
    'abstract': '自然语言处理是人工智能领域的重要研究方向，近年来随着深度学习技术的发展，该领域取得了突破性进展。本文系统综述了深度学习在自然语言处理中的应用，包括词向量表示、序列标注、文本分类、机器翻译等核心任务。首先介绍了神经网络语言模型和词嵌入技术的基本原理；其次分析了卷积神经网络、循环神经网络和Transformer等深度学习架构在NLP任务中的应用；然后讨论了预训练语言模型（如BERT、GPT）的最新进展；最后展望了未来发展趋势和面临的挑战。研究表明，深度学习技术显著提升了自然语言处理系统的性能，但仍存在可解释性、数据依赖等问题需要解决。',
    'introduction': '自然语言处理（Natural Language Processing，NLP）是计算机科学、人工智能和语言学的交叉学科，旨在使计算机能够理解、处理和生成人类语言。随着互联网和大数据技术的快速发展，自然语言处理技术在信息检索、智能问答、机器翻译、情感分析等领域得到了广泛应用[1]。\n\n近年来，深度学习（Deep Learning）技术的兴起为自然语言处理带来了革命性的变化。传统的NLP方法依赖于人工设计的特征和规则，而深度学习方法能够自动学习数据的层次化表示，显著提升了各项任务的性能[2]。特别是2018年以来，以BERT、GPT为代表的预训练语言模型（Pre-trained Language Models，PLMs）的出现，使得自然语言处理进入了新的发展阶段[3]。\n\n本文旨在系统综述深度学习技术在自然语言处理领域的研究进展，分析主要技术方法的特点和适用场景，并探讨未来发展方向。',
    'literature_review': '自然语言处理的研究可以追溯到20世纪50年代。早期的研究主要基于规则方法，依赖语言学专家手工编写语法规则[4]。20世纪90年代，统计机器学习方法开始兴起，隐马尔可夫模型（HMM）、条件随机场（CRF）等概率图模型被广泛应用于词性标注、命名实体识别等任务[5]。\n\n（一）神经网络语言模型\n\n神经网络语言模型是深度学习在NLP中的早期应用。Bengio等人于2003年提出了神经网络概率语言模型（NPLM），首次使用神经网络学习词的分布式表示[6]。Mikolov等人在2013年提出的Word2Vec模型，通过Skip-gram和CBOW两种架构高效地学习词向量，开启了词嵌入（Word Embedding）的研究热潮[7]。\n\n（二）深度学习架构\n\n1. 卷积神经网络（CNN）最初应用于图像处理领域，后被引入文本分类任务。Kim在2014年提出的TextCNN模型使用不同大小的卷积核提取文本的局部特征，在情感分析等任务上取得了良好效果[8]。\n\n2. 循环神经网络（RNN）及其变体LSTM、GRU特别适合处理序列数据，在机器翻译、文本生成等任务中表现优异[9]。 seq2seq框架结合注意力机制，成为神经机器翻译的标准架构[10]。\n\n3. Transformer架构完全基于自注意力机制，摒弃了循环结构，实现了高效的并行计算。BERT采用双向Transformer编码器，通过掩码语言模型和下一句预测进行预训练，在多项NLP任务中取得突破性成果[11]。',
    'methodology': '本文采用文献综述方法，系统分析了2015年至2024年间发表在ACL、EMNLP、NAACL、AAAI等顶级会议以及Computational Linguistics、TACL等期刊上的相关论文。\n\n（一）文献检索策略\n\n1. 在Google Scholar、ACL Anthology、IEEE Xplore等学术数据库中进行关键词检索，检索词包括"deep learning"、"natural language processing"、"pre-trained language models"、"transformer"等；\n\n2. 采用滚雪球方法，通过参考文献追溯相关研究；\n\n3. 重点关注高被引论文和获奖论文。\n\n（二）分类体系\n\n本文从技术方法角度对文献进行分类，主要涵盖以下几个维度：\n\n- 基础技术：词嵌入、神经网络架构\n- 核心任务：分类、序列标注、生成\n- 应用场景：机器翻译、问答系统、文本摘要\n- 前沿方向：大语言模型、多模态学习',
    'results': '通过对近年来深度学习在NLP领域的研究进展进行系统分析，得到以下主要发现：\n\n（一）技术发展脉络\n\n从技术演进角度看，深度学习在NLP中的应用经历了三个主要阶段：\n\n1. 词嵌入阶段（2013-2016）：以Word2Vec、GloVe为代表，学习词的分布式表示；\n\n2. 序列建模阶段（2014-2018）：RNN、CNN、Attention等架构的发展与应用；\n\n3. 预训练模型阶段（2018至今）：BERT、GPT等预训练-微调范式的兴起。\n\n（二）性能提升效果\n\n表1展示了不同方法在GLUE基准测试上的性能对比。可以看出，预训练语言模型相比传统方法有显著提升。\n\n（三）应用拓展情况\n\n深度学习NLP技术已在多个垂直领域得到应用，包括医疗文本分析、法律文档处理、金融舆情监测等。',
    'discussion': '虽然深度学习技术极大地推动了自然语言处理的发展，但仍存在一些值得关注的问题和挑战。\n\n（一）可解释性问题\n\n深度神经网络通常被视为"黑盒"模型，其决策过程难以解释。在医疗、法律等高风险应用领域，模型的可解释性至关重要[12]。近年来，注意力可视化、LIME、SHAP等方法被提出用于解释模型预测，但距离完全理解模型行为仍有差距。\n\n（二）数据依赖问题\n\n深度学习模型通常需要大量标注数据进行训练。对于低资源语言和专业领域，获取足够的训练数据往往困难且昂贵[13]。迁移学习和少样本学习是应对这一挑战的主要研究方向。\n\n（三）伦理与社会影响\n\n大语言模型可能产生有偏见、有毒或不真实的输出，带来潜在的伦理风险[14]。如何开发更安全、更负责任的语言模型是学术界和工业界共同关注的问题。',
    'conclusion': '本文系统综述了深度学习在自然语言处理领域的研究进展。主要结论如下：\n\n（一）深度学习技术已成为自然语言处理的主流方法，显著提升了各项任务的性能指标。\n\n（二）预训练语言模型代表了当前最先进的技术水平，通过大规模无监督预训练和有监督微调，在多个NLP任务上取得了突破性进展。\n\n（三）未来研究应关注模型的可解释性、数据效率、安全性和伦理问题，推动自然语言处理技术向更加实用、可信的方向发展。\n\n随着计算能力的提升和算法的改进，自然语言处理技术将在更多领域发挥重要作用，为人机交互、知识获取和信息传播带来新的可能。',
    'references': '[1] Manning C D, Schütze H. Foundations of Statistical Natural Language Processing[M]. Cambridge: MIT Press, 1999.\n[2] Young T, Hazarika D, Poria S, et al. Recent trends in deep learning based natural language processing[J]. IEEE Computational Intelligence Magazine, 2018, 13(3): 55-75.\n[3] Qiu X P, Sun T X, Xu Y G, et al. Pre-trained models for natural language processing: A survey[J]. Science China Technological Sciences, 2020, 63(10): 1872-1897.\n[4] Joshi A K. Natural language processing[J]. Science, 1991, 253(5021): 1242-1249.\n[5] Lafferty J, McCallum A, Pereira F C N. Conditional random fields: Probabilistic models for segmenting and labeling sequence data[C]//Proceedings of the 18th International Conference on Machine Learning. 2001: 282-289.\n[6] Bengio Y, Ducharme R, Vincent P, et al. A neural probabilistic language model[J]. Journal of Machine Learning Research, 2003, 3: 1137-1155.\n[7] Mikolov T, Sutskever I, Chen K, et al. Distributed representations of words and phrases and their compositionality[C]//Advances in Neural Information Processing Systems. 2013: 3111-3119.\n[8] Kim Y. Convolutional neural networks for sentence classification[C]//Proceedings of the 2014 Conference on Empirical Methods in Natural Language Processing. 2014: 1746-1751.\n[9] Hochreiter S, Schmidhuber J. Long short-term memory[J]. Neural Computation, 1997, 9(8): 1735-1780.\n[10] Bahdanau D, Cho K, Bengio Y. Neural machine translation by jointly learning to align and translate[C]//International Conference on Learning Representations. 2015.\n[11] Devlin J, Chang M W, Lee K, et al. BERT: Pre-training of deep bidirectional transformers for language understanding[C]//Proceedings of NAACL-HLT. 2019: 4171-4186.\n[12] Belinkov Y, Glass J. Analysis methods in neural language processing: A survey[J]. Transactions of the Association for Computational Linguistics, 2019, 7: 49-72.\n[13] Hirschberg J, Manning C D. Advances in natural language processing[J]. Science, 2015, 349(6245): 261-266.\n[14] Bender E M, Gebru T, McMillan-Major A, et al. On the dangers of stochastic parrots: Can language models be too big?[C]//Proceedings of the 2021 ACM Conference on Fairness, Accountability, and Transparency. 2021: 610-623.'
}

# 元数据
metadata = {
    'title': '基于深度学习的自然语言处理研究进展',
    'keywords': ['深度学习', '自然语言处理', '预训练模型', 'Transformer', 'BERT'],
    'field': '人工智能',
    'citation_style': 'gbt7714',
    'language': 'chinese'
}

# 生成论文
generator = DocxGenerator()
output_path = Path('output/chinese_paper_sample.docx')
output_path.parent.mkdir(parents=True, exist_ok=True)

generated_path = generator.generate_paper(sections, metadata, output_path)
print(f"中文论文已生成：{generated_path}")
