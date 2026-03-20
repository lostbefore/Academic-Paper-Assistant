export const translations = {
  english: {
    // Common
    appName: 'Academic Paper Assistant',
    appDescription: 'AI-powered academic paper generation',
    loading: 'Loading...',
    error: 'Error',
    save: 'Save',
    cancel: 'Cancel',
    delete: 'Delete',
    edit: 'Edit',
    create: 'Create',
    back: 'Back',
    next: 'Next',
    previous: 'Previous',
    submit: 'Submit',
    download: 'Download',
    view: 'View',
    search: 'Search',
    close: 'Close',

    // Navigation
    nav: {
      home: 'Home',
      myPapers: 'My Papers',
      newPaper: 'New Paper',
    },

    // Home / Dashboard
    dashboard: {
      welcome: 'Welcome to Academic Paper Assistant',
      welcomeDesc: 'Generate high-quality academic papers with AI assistance. Supports multiple citation styles including APA, MLA, IEEE, and GB/T7714.',
      createNewPaper: 'Create New Paper',
      viewPapers: 'View Papers',
      totalPapers: 'Total Papers',
      completed: 'Completed',
      inProgress: 'In Progress',
      features: {
        generate: {
          title: 'Generate Paper',
          desc: 'Create a complete academic paper with AI assistance',
        },
        manage: {
          title: 'My Papers',
          desc: 'View and manage your generated papers',
        },
      },
      recentPapers: 'Recent Papers',
      viewAll: 'View All',
      noPapersYet: 'No papers yet',
      apiConfig: 'API Configuration',
      apiKey: 'API Key',
      model: 'Model',
      apiBase: 'API Base',
      citationStyles: 'Citation Styles',
      languages: 'Languages',
      configured: 'Configured',
      notConfigured: 'Not Configured',
    },

    // Paper List
    paperList: {
      title: 'My Papers',
      paperCount: 'papers generated',
      noPapers: 'No papers yet',
      noPapersDesc: 'Create your first academic paper using our AI-powered generator',
      createPaper: 'Create Paper',
      viewDetails: 'View Details',
      qualityScore: 'Quality Score',
      confirmDelete: 'Are you sure you want to delete this paper?',
    },

    // Create Paper
    createPaper: {
      title: 'Create New Paper',
      subtitle: 'Fill in the details below to generate your academic paper',
      steps: {
        basicInfo: {
          title: 'Basic Info',
          desc: 'Title and research field',
        },
        keywords: {
          title: 'Keywords',
          desc: 'Add research keywords',
        },
        settings: {
          title: 'Settings',
          desc: 'Length and citation style',
        },
      },
      paperTitle: 'Paper Title',
      paperTitlePlaceholder: 'e.g., A Survey on Hallucination Detection in Large Language Models',
      paperTitleHelp: 'Enter a clear and descriptive title for your research',
      researchField: 'Research Field',
      researchFieldPlaceholder: 'e.g., Artificial Intelligence, Computer Science, Psychology',
      researchFieldHelp: 'Specify the academic field or discipline',
      researchKeywords: 'Research Keywords',
      keywordPlaceholder: 'Add a keyword and press Enter',
      keywordHelp: 'Add keywords to help the AI understand your research focus',
      noKeywords: 'No keywords added yet. Keywords help improve paper relevance.',
      paperLength: 'Paper Length',
      lengths: {
        short: {
          label: 'Short',
          desc: '~3000 words',
        },
        medium: {
          label: 'Medium',
          desc: '~6000 words',
        },
        long: {
          label: 'Long',
          desc: '~10000 words',
        },
      },
      citationStyle: 'Citation Style',
      language: 'Language / 语言',
      languages: {
        english: {
          label: 'English',
          desc: 'Generate paper in English',
        },
        chinese: {
          label: '中文',
          desc: '生成中文论文',
        },
      },
      requiredFields: 'Please fill in all required fields',
      generatePaper: 'Generate Paper',
      generating: 'Generating...',
    },

    // Paper Viewer
    paperViewer: {
      processing: 'Processing...',
      download: 'Download',
      downloadDocx: 'Download Word (DOCX)',
      downloadMarkdown: 'Download Markdown (MD)',
      downloadPdf: 'Download PDF',
      downloadProgress: {
        preparing: 'Preparing...',
        generating: 'Generating document...',
        formatting: 'Formatting content...',
        addingImages: 'Adding images...',
        finalizing: 'Finalizing...',
        downloading: 'Downloading...',
        success: 'Download complete!',
        failed: 'Download failed',
        pdfFailed: 'PDF conversion failed. Please ensure Microsoft Word or LibreOffice is installed.',
      },
      paperContent: 'Paper Content',
      sections: 'Sections',
      abstract: 'Abstract',
      introduction: 'Introduction',
      literatureReview: 'Literature Review',
      methodology: 'Methodology',
      results: 'Results',
      discussion: 'Discussion',
      conclusion: 'Conclusion',
      references: 'References',
      paperNotFound: 'Paper Not Found',
      paperNotFoundDesc: "The paper you're looking for doesn't exist",
      backToPapers: 'Back to Papers',
      formattedPreview: 'Formatted Preview',
      plainPreview: 'Plain Preview',
      progressSteps: {
        research: 'Research',
        writing: 'Writing',
        complete: 'Complete',
      },
    },

    // Status
    status: {
      generating: 'generating',
      writing: 'writing',
      completed: 'completed',
      failed: 'failed',
    },

    // Footer
    footer: {
      description: 'AI-powered academic paper generation',
      supports: 'Supports APA, MLA, IEEE, GB/T7714',
    },
  },

  chinese: {
    // Common
    appName: '学术论文助手',
    appDescription: 'AI 驱动的学术论文生成',
    loading: '加载中...',
    error: '错误',
    save: '保存',
    cancel: '取消',
    delete: '删除',
    edit: '编辑',
    create: '创建',
    back: '返回',
    next: '下一步',
    previous: '上一步',
    submit: '提交',
    download: '下载',
    view: '查看',
    search: '搜索',
    close: '关闭',

    // Navigation
    nav: {
      home: '首页',
      myPapers: '我的论文',
      newPaper: '新建论文',
    },

    // Home / Dashboard
    dashboard: {
      welcome: '欢迎使用学术论文助手',
      welcomeDesc: '使用 AI 辅助生成高质量学术论文。支持 APA、MLA、IEEE 和 GB/T7714 等多种引用格式。',
      createNewPaper: '创建新论文',
      viewPapers: '查看论文',
      totalPapers: '论文总数',
      completed: '已完成',
      inProgress: '进行中',
      features: {
        generate: {
          title: '生成论文',
          desc: '使用 AI 辅助创建完整的学术论文',
        },
        manage: {
          title: '我的论文',
          desc: '查看和管理您生成的论文',
        },
      },
      recentPapers: '最近论文',
      viewAll: '查看全部',
      noPapersYet: '暂无论文',
      apiConfig: 'API 配置',
      apiKey: 'API 密钥',
      model: '模型',
      apiBase: 'API 地址',
      citationStyles: '引用格式',
      languages: '语言支持',
      configured: '已配置',
      notConfigured: '未配置',
    },

    // Paper List
    paperList: {
      title: '我的论文',
      paperCount: '篇已生成论文',
      noPapers: '暂无论文',
      noPapersDesc: '使用我们的 AI 论文生成器创建您的第一篇学术论文',
      createPaper: '创建论文',
      viewDetails: '查看详情',
      qualityScore: '质量评分',
      confirmDelete: '确定要删除这篇论文吗？',
    },

    // Create Paper
    createPaper: {
      title: '创建新论文',
      subtitle: '填写以下信息以生成您的学术论文',
      steps: {
        basicInfo: {
          title: '基本信息',
          desc: '标题和研究领域',
        },
        keywords: {
          title: '关键词',
          desc: '添加研究关键词',
        },
        settings: {
          title: '设置',
          desc: '篇幅和引用格式',
        },
      },
      paperTitle: '论文标题',
      paperTitlePlaceholder: '例如：大型语言模型幻觉检测综述',
      paperTitleHelp: '为您的研究输入一个清晰描述性的标题',
      researchField: '研究领域',
      researchFieldPlaceholder: '例如：人工智能、计算机科学、心理学',
      researchFieldHelp: '指定学术领域或学科',
      researchKeywords: '研究关键词',
      keywordPlaceholder: '添加关键词并按回车',
      keywordHelp: '添加关键词以帮助 AI 理解您的研究重点',
      noKeywords: '尚未添加关键词。关键词有助于提高论文相关性。',
      paperLength: '论文篇幅',
      lengths: {
        short: {
          label: '短篇',
          desc: '约3000字',
        },
        medium: {
          label: '中篇',
          desc: '约6000字',
        },
        long: {
          label: '长篇',
          desc: '约10000字',
        },
      },
      citationStyle: '引用格式',
      language: '语言 / Language',
      languages: {
        english: {
          label: 'English',
          desc: 'Generate paper in English',
        },
        chinese: {
          label: '中文',
          desc: '生成中文论文',
        },
      },
      requiredFields: '请填写所有必填字段',
      generatePaper: '生成论文',
      generating: '生成中...',
    },

    // Paper Viewer
    paperViewer: {
      processing: '处理中...',
      download: '下载',
      downloadDocx: '下载 Word (DOCX)',
      downloadMarkdown: '下载 Markdown (MD)',
      downloadPdf: '下载 PDF',
      downloadProgress: {
        preparing: '准备中...',
        generating: '正在生成文档...',
        formatting: '正在格式化内容...',
        addingImages: '正在添加图片...',
        finalizing: '正在完成...',
        downloading: '正在下载...',
        success: '下载完成！',
        failed: '下载失败',
        pdfFailed: 'PDF转换失败。请确保已安装 Microsoft Word 或 LibreOffice。',
      },
      paperContent: '论文内容',
      sections: '章节',
      abstract: '摘要',
      introduction: '引言',
      literatureReview: '文献综述',
      methodology: '研究方法',
      results: '研究结果',
      discussion: '讨论',
      conclusion: '结论',
      references: '参考文献',
      paperNotFound: '未找到论文',
      paperNotFoundDesc: '您要查找的论文不存在',
      backToPapers: '返回论文列表',
      formattedPreview: '格式化预览',
      plainPreview: '纯文本预览',
      progressSteps: {
        research: '研究',
        writing: '写作',
        complete: '完成',
      },
    },

    // Status
    status: {
      generating: '研究中',
      writing: '写作中',
      completed: '已完成',
      failed: '失败',
    },

    // Footer
    footer: {
      description: 'AI 驱动的学术论文生成',
      supports: '支持 APA、MLA、IEEE、GB/T7714',
    },
  },
} as const;

export type Language = 'english' | 'chinese';
export type Translations = typeof translations;
