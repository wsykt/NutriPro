export interface TrainingExercise {
  name: string
  level: '入门' | '入门 - 中级' | '中级' | '中高级' | '高级'
  description: string
  met: number
  sets?: string
}

export interface TrainingMuscleGroup {
  key: string
  label: string
  color: string
  exercises: TrainingExercise[]
}

export const trainingMuscleGroups: TrainingMuscleGroup[] = [
  {
    key: 'chest',
    label: '胸肌',
    color: '#ff8a65',
    exercises: [
      { name: '墙壁俯卧撑', level: '入门', description: '站立靠墙俯卧撑，适合初学者与老年人', met: 3.5 },
      { name: '跪姿俯卧撑', level: '入门', description: '膝盖着地，降低负重，衔接墙壁俯卧撑与标准俯卧撑', met: 5.0 },
      { name: '器械坐姿推胸', level: '入门 - 中级', description: '轨迹稳定，适合新手建立胸肌发力感', met: 5.2 },
      { name: '绳索上斜夹胸', level: '中级', description: '针对上胸内侧，顶峰收缩感强', met: 5.5 },
      { name: '绳索夹胸', level: '中级', description: '固定轨迹挤压胸肌，侧重胸肌中缝', met: 5.8 },
      { name: '平板哑铃卧推', level: '中级', description: '平板哑铃卧推，全胸肌激活', met: 6.0 },
      { name: '上斜哑铃卧推', level: '中级', description: '上斜角度，侧重刺激上胸肌', met: 6.2 },
      { name: '下斜哑铃卧推', level: '中级', description: '倾斜角度，重点强化下胸区域', met: 7.0 },
      { name: '下斜杠铃卧推', level: '高级', description: '向下倾斜，强化下胸肌群，负重上限更高', met: 7.8 },
      { name: '标准俯卧撑', level: '中级', description: '标准俯卧撑，锻炼胸大肌与三头肌', met: 8.0 },
      { name: '宽距俯卧撑', level: '中级', description: '加大手臂间距，侧重胸大肌外侧', met: 8.2 },
      { name: '双杠臂屈伸（侧重胸部）', level: '中高级', description: '身体前倾，重点锻炼下胸，附带三头肌', met: 8.3 },
      { name: '窄距俯卧撑', level: '中高级', description: '手臂贴近躯干，兼顾胸内侧与肱三头肌', met: 8.5 }
    ]
  },
  {
    key: 'deltoid-middle',
    label: '三角肌中束',
    color: '#60a5fa',
    exercises: [
      { name: '弹力带侧平举', level: '入门', description: '弹力带侧平举，负荷柔和，适合新手建立发力感', met: 3.2 },
      { name: '哑铃侧平举', level: '入门', description: '站姿哑铃侧平举，三角肌中束经典孤立动作', met: 4.1 },
      { name: '器械侧平举', level: '入门 - 中级', description: '固定运动轨迹，躯干不易晃动', met: 4.4 },
      { name: '绳索侧平举', level: '中级', description: '全程持续张力，避免借力摆动', met: 4.7 },
      { name: '俯身哑铃侧平举（侧重中束外侧）', level: '中级', description: '微调体态强化中束远端刺激', met: 5.1 },
      { name: '坐姿哑铃侧平举', level: '中级', description: '限制身体摆动，减少代偿', met: 5.3 },
      { name: '宽握直立划船', level: '中高级', description: '重点刺激三角肌中束，注意控制肘关节高度', met: 5.8 },
      { name: '站姿哑铃推举', level: '中级', description: '活动空间充足，均衡刺激肩部肌群', met: 6.5 },
      { name: '杠铃推举', level: '中级', description: '肩部整体发力，中束协同参与', met: 6.8 }
    ]
  },
  {
    key: 'deltoid-posterior',
    label: '三角肌后束',
    color: '#8b5cf6',
    exercises: [
      { name: '弹力带面拉', level: '入门', description: '弹力带面拉，改善圆肩，激活后束', met: 3.4 },
      { name: '俯身弹力带飞鸟', level: '入门', description: '俯身姿态，低负荷感受后束收缩', met: 3.8 },
      { name: '器械反向飞鸟', level: '入门 - 中级', description: '轨迹稳定，新手友好，降低腰部压力', met: 4.3 },
      { name: '俯身哑铃飞鸟', level: '中级', description: '经典后束孤立训练，注意肩胛骨控制', met: 4.6 },
      { name: '绳索面拉', level: '中级', description: '持续拉力，后束顶峰收缩明显', met: 5.0 },
      { name: '俯身绳索飞鸟', level: '中级', description: '全程保持张力，减少身体晃动代偿', met: 5.2 },
      { name: '坐姿俯身哑铃飞鸟', level: '中级', description: '坐姿稳定躯干，专注三角肌后束发力', met: 5.5 },
      { name: '反向哑铃推举', level: '中高级', description: '强化肩后束与肩袖肌群', met: 6.1 },
      { name: '杠铃俯身划船（后束协同）', level: '中高级', description: '背部训练同时带动三角肌后束参与', met: 7.2 }
    ]
  },
  {
    key: 'biceps',
    label: '肱二头肌',
    color: '#fbbf24',
    exercises: [
      { name: '弹力带弯举', level: '入门', description: '弹力带弯举，关节友好', met: 3.5 },
      { name: '器械二头弯举', level: '入门 - 中级', description: '固定轨迹，新手容易找到发力感', met: 4.2 },
      { name: '哑铃弯举', level: '入门', description: '坐姿哑铃弯举，孤立肱二头肌', met: 4.5 },
      { name: '绳索弯举', level: '中级', description: '全程持续张力，二头肌收缩感强烈', met: 4.7 },
      { name: '交替站姿哑铃弯举', level: '中级', description: '单侧发力，纠正左右力量差距', met: 4.8 },
      { name: '站姿杠铃弯举', level: '中级', description: '基础复合动作，均衡刺激长短头', met: 5.0 },
      { name: '集中弯举', level: '中级', description: '单侧顶峰收缩，强化二头肌峰', met: 5.2 },
      { name: '斜托弯举（牧师凳弯举）', level: '中级', description: '限制肩部借力，精准孤立二头肌', met: 5.3 },
      { name: '宽握杠铃弯举', level: '中高级', description: '重点刺激肱二头肌长头', met: 5.5 }
    ]
  },
  {
    key: 'obliques',
    label: '腹外斜肌',
    color: '#ec4899',
    exercises: [
      { name: '站立侧弯', level: '入门', description: '哑铃站立侧弯，腹斜肌拉伸收紧', met: 3 },
      { name: '弹力带旋转抗阻', level: '入门', description: '站姿弹力带转体，温和旋转刺激侧腹', met: 3.6 },
      { name: '仰卧触膝转体', level: '入门', description: '简易旋转核心动作，降低腰背压力', met: 3.9 },
      { name: '俄罗斯转体', level: '中级', description: '坐姿核心旋转，激活侧腹', met: 4.5 },
      { name: '侧卧卷腹', level: '中级', description: '针对性收缩单侧腹外斜肌', met: 4.6 },
      { name: '绳索旋转转体', level: '中级', description: '持续张力，精准刺激腹外斜肌', met: 4.8 },
      { name: '侧平板支撑', level: '中级', description: '静态维持，强化侧腹耐力', met: 5.0 },
      { name: '登山转体', level: '中级', description: '动态扭转，兼顾核心整体与侧腹', met: 5.3 },
      { name: '杠铃杆旋转伐木', level: '中高级', description: '模拟伐木动作，大幅度旋转侧腹', met: 5.7 },
      { name: '悬垂举腿转体', level: '中高级', description: '悬垂姿态旋转，侧腹高强度发力', met: 6.1 }
    ]
  },
  {
    key: 'abs',
    label: '腹肌',
    color: '#43b086',
    exercises: [
      { name: '站立卷腹', level: '入门', description: '站立拉力绳卷腹，老年友好', met: 3.5 },
      { name: '平板支撑', level: '入门', description: '全核心稳定训练，适合各人群', met: 4 },
      { name: '死虫式', level: '入门 - 中级', description: '稳定腰椎，均衡锻炼上下腹', met: 5.0 },
      { name: '仰卧卷腹', level: '中级', description: '标准卷腹，激活上腹部', met: 5.5 },
      { name: '反向卷腹', level: '中级', description: '重点针对下腹，减少髂腰肌代偿', met: 6.0 },
      { name: '绳索卷腹', level: '中高级', description: '持续负重张力，上腹深度刺激', met: 6.4 },
      { name: '卷腹触足', level: '中高级', description: '增大收缩幅度，强化上腹顶峰挤压', met: 6.6 },
    ]
  },
  {
    key: 'adductors',
    label: '大腿内收肌',
    color: '#14b8a6',
    exercises: [
      { name: '侧卧腿内收', level: '入门', description: '侧卧弹力带腿内收，老年友好', met: 3 },
      { name: '坐姿夹球', level: '入门', description: '坐姿瑜伽球内收，内收肌激活', met: 3.5 },
      { name: '器械坐姿内收', level: '入门 - 中级', description: '固定轨迹，可控负荷，新手首选', met: 4.0 },
      { name: '弹力带站姿内收', level: '入门 - 中级', description: '站立姿态，模拟日常发力模式', met: 4.2 },
      { name: '相扑静蹲', level: '中级', description: '宽距静态蹲，持续刺激大腿内侧', met: 4.7 },
      { name: '宽距箭步蹲', level: '中级', description: '大幅度步距，拉伸并发力内收肌群', met: 5.1 },
      { name: '侧卧负重内收', level: '中级', description: '增加哑铃负重，提升训练强度', met: 5.4 },
      { name: '绳索站姿内收', level: '中级', description: '全程保持持续张力，孤立内侧肌群', met: 5.6 },
      { name: '蛙式静撑', level: '中高级', description: '俯卧蛙姿静态保持，深度激活内收肌', met: 6.0 },
      { name: '宽距硬拉（内收协同）', level: '中高级', description: '复合动作，兼顾臀腿与大腿内收肌', met: 6.8 }
    ]
  },
  {
    key: 'quadriceps',
    label: '股四头肌',
    color: '#f97316',
    exercises: [
      { name: '椅背辅助深蹲', level: '入门', description: '靠椅背辅助深蹲，老年安全版', met: 4.5 },
      { name: '静蹲', level: '入门 - 中级', description: '静态维持，适合关节不适人群', met: 4.9 },
      { name: '器械坐姿伸膝', level: '入门 - 中级', description: '孤立股四头肌，负荷易于调控', met: 5.2 },
      { name: '腿举', level: '中级', description: '坐姿腿举机，膝关节友好', met: 6.5 },
      { name: '哈克深蹲', level: '中级', description: '躯干支撑稳定，聚焦股四头肌', met: 6.8 },
      { name: '箭步蹲', level: '中级', description: '单侧发力，均衡左右腿部力量', met: 7.1 },
      { name: '保加利亚分腿蹲', level: '中级', description: '稳定要求高，侧重股四头肌刺激', met: 7.6 },
      { name: '箱式深蹲', level: '中高级', description: '控制下蹲幅度，减少腰部代偿', met: 8.1 },
      { name: '深蹲', level: '中级', description: '基础复合动作，全腿部激活', met: 8 },
      { name: '前深蹲', level: '中高级', description: '重心前移，重点强化股四头肌', met: 8.4 }
    ]
  },
  {
    key: 'tibialis-anterior',
    label: '胫骨前肌',
    color: '#06b6d4',
    exercises: [
      { name: '脚尖上勾', level: '入门', description: '坐姿或站立脚背上勾，激活胫骨前肌', met: 2.5 },
      { name: '行走脚跟步', level: '入门', description: '踮起脚跟行走，锻炼胫骨前肌', met: 3 },
      { name: '弹力带足背屈', level: '入门 - 中级', description: '弹力带抗阻勾脚，增加负荷刺激', met: 3.6 },
      { name: '坐姿负重足背屈', level: '入门 - 中级', description: '脚掌放置重物，强化足背屈发力', met: 4.0 },
      { name: '台阶勾脚训练', level: '中级', description: '前脚掌搭台阶，充分伸展收缩胫骨前肌', met: 4.3 },
      { name: '器械足背屈', level: '中级', description: '专用器械稳定发力，精准孤立肌群', met: 4.6 },
      { name: '单腿脚跟步行', level: '中级', description: '单腿脚跟行走，提升平衡与单侧耐力', met: 4.9 },
      { name: '斜坡脚跟行走', level: '中高级', description: '上坡脚跟行进，持续加大胫骨前肌负荷', met: 5.4 }
    ]
  },
  {
    key: 'upper-back',
    label: '上背 / 菱形肌',
    color: '#3b82f6',
    exercises: [
      { name: '弹力带划船', level: '入门', description: '站姿弹力带划船，老年友好', met: 4 },
      { name: '器械坐姿划船', level: '入门 - 中级', description: '轨迹稳定，易于感受肩胛骨内收发力', met: 4.8 },
      { name: '坐姿绳索划船', level: '入门', description: '坐姿绳索划船，锻炼上背与菱形肌', met: 5.5 },
      { name: '反向飞鸟', level: '中级', description: '侧重肩胛骨内收，强化菱形肌上部', met: 5.7 },
      { name: '俯身哑铃划船', level: '中级', description: '单侧控制，强化菱形肌与中背部', met: 5.9 },
      { name: '单臂绳索划船', level: '中级', description: '改善左右肌力不平衡，孤立中背部', met: 6.3 },
      { name: '俯身杠铃划船', level: '中级', description: '经典复合动作，大面积刺激上背肌群', met: 6.6 },
      { name: '引体向上（宽握，沉肩控制）', level: '中高级', description: '自重复合动作，上背整体协同发力', met: 7.8 },
      { name: '硬拉（上背等长稳定）', level: '中高级', description: '维持肩胛骨收紧，静态强化菱形肌', met: 8.0 }
    ]
  },
  {
    key: 'triceps',
    label: '肱三头肌',
    color: '#f59e0b',
    exercises: [
      { name: '弹力带下压', level: '入门', description: '弹力带三头下压，关节友好', met: 3.5 },
      { name: '器械肱三头伸展', level: '入门 - 中级', description: '轨道固定，新手容易掌握发力', met: 4.2 },
      { name: '绳索下压', level: '入门', description: '绳索下压三头，孤立肱三头肌', met: 4.5 },
      { name: '仰卧哑铃臂屈伸', level: '入门 - 中级', description: '侧重刺激三头长头', met: 4.9 },
      { name: '俯身绳索臂屈伸', level: '中级', description: '固定躯干，精准孤立三头外侧头', met: 5.1 },
      { name: '颈后哑铃臂屈伸', level: '中级', description: '充分拉伸长头，增大活动幅度', met: 5.6 },
      { name: '杠铃仰卧臂屈伸', level: '中级', description: '长头深度刺激，可逐步加重', met: 5.8 },
      { name: '站姿绳索颈后臂屈伸', level: '中高级', description: '持续张力，强化三头长头', met: 6.0 },
      { name: '双杠臂屈伸（侧重三头）', level: '中高级', description: '身体直立，重点锻炼肱三头肌', met: 7.9 }
    ]
  },
  {
    key: 'lower-back',
    label: '下背 / 竖脊肌',
    color: '#6366f1',
    exercises: [
      { name: '猫牛式伸展', level: '入门', description: '瑜伽猫牛式，脊柱活动，老年适合', met: 2.5 },
      { name: '超人式伸展', level: '入门', description: '俯卧双臂双腿上抬，激活竖脊肌', met: 4 },
      { name: '俯卧静态挺身', level: '入门 - 中级', description: '俯卧保持身体抬起，等长强化下背', met: 4.6 },
      { name: '弹力带早安式', level: '入门 - 中级', description: '弹力带负重屈髋，温和刺激竖脊肌', met: 4.9 },
      { name: '器械背屈伸', level: '中级', description: '罗马椅挺身，针对性锻炼下背部', met: 5.5 },
      { name: '杠铃早安式', level: '中级', description: '屈髋后伸，竖脊肌持续稳定发力', met: 6.2 },
      { name: '俯身杠铃划船（下背稳定）', level: '中级', description: '等长收紧竖脊肌，提升腰背耐力', met: 6.6 },
      { name: '山羊挺身负重版', level: '中高级', description: '胸前负重罗马椅挺身，加大负荷', met: 6.9 },
      { name: '传统罗马尼亚硬拉', level: '中高级', description: '侧重后侧链，强化下背与臀腘绳肌', met: 7.7 },
      { name: '硬拉', level: '中高级', description: '经典复合动作，高强度刺激竖脊肌', met: 8.2 }
    ]
  },
  {
    key: 'glutes',
    label: '臀肌',
    color: '#ec4899',
    exercises: [
      { name: '髋外展器械', level: '入门 - 中级', description: '坐姿髋外展，孤立臀中肌', met: 4.7 },
      { name: '弹力带蚌式开合', level: '入门 - 中级', description: '侧卧髋外展，侧重臀中肌，改善臀凹陷', met: 4.8 },
      { name: '臀桥', level: '入门', description: '仰卧臀桥，激活臀大肌，各人群适合', met: 5 },
      { name: '弹力带侧向行走', level: '入门 - 中级', description: '横向移步，持续激活臀中肌', met: 5.1 },
      { name: '后踢腿（绳索）', level: '中级', description: '站姿绳索后摆腿，孤立刺激臀大肌', met: 5.3 },
      { name: '负重臀桥', level: '中级', description: '背部放置杠铃片，提升臀大肌刺激强度', met: 5.6 },
      { name: '单腿臀桥', level: '中高级', description: '单侧发力，平衡左右臀部力量', met: 5.9 },
      { name: '臀推', level: '中级', description: '器械臀推，大幅度挤压臀大肌', met: 6.2 },
      { name: '反向箭步蹲', level: '中级', description: '重心靠后，优先调动臀部肌群', met: 6.5 },
      { name: '相扑深蹲', level: '中级', description: '宽站距深蹲，侧重臀大肌下部', met: 6.8 },
      { name: '罗马尼亚硬拉', level: '中级', description: '后侧链训练，臀大肌与腘绳肌协同发力', met: 7.0 }
    ]
  },
  {
    key: 'hamstrings',
    label: '腘绳肌',
    color: '#d946ef',
    exercises: [
      { name: '仰卧弹力带腿弯举', level: '入门', description: '仰卧屈膝抗阻，适合腰部不适人群', met: 3.7 },
      { name: '站立腿弯举', level: '入门', description: '站姿弹力带弯腿，老年友好', met: 4 },
      { name: '坐姿弹力带腿弯举', level: '入门 - 中级', description: '坐姿抗阻屈膝，温和刺激后侧大腿', met: 4.4 },
      { name: '绳索站姿腿弯举', level: '中级', description: '持续张力，精准孤立后侧肌群', met: 4.8 },
      { name: '俯卧腿弯举', level: '中级', description: '俯卧腿弯举机，孤立腘绳肌', met: 5 },
      { name: '坐姿腿弯举', level: '中级', description: '坐姿器械弯举，降低腰部压力', met: 5.2 },
      { name: '哑铃直腿硬拉', level: '中级', description: '控制屈膝幅度，重点拉伸收缩腘绳肌', met: 5.6 },
      { name: '单腿罗马尼亚硬拉', level: '中高级', description: '单侧稳定，改善两侧肌力不均', met: 6.7 },
      { name: '北欧腿弯举', level: '中高级', description: '自重离心训练，高强度刺激腘绳肌', met: 7.5 }
    ]
  },
  {
    key: 'calves',
    label: '小腿三头肌',
    color: '#0ea5e9',
    exercises: [
      { name: '坐姿提踵', level: '入门', description: '坐姿提踵，比目鱼肌为主', met: 3.5 },
      { name: '站立提踵', level: '入门', description: '双腿站立提踵，腓肠肌', met: 4 },
      { name: '弹力带坐姿提踵', level: '入门 - 中级', description: '弹力带增加负荷，侧重比目鱼肌', met: 4.2 },
      { name: '斜坡站立提踵', level: '中级', description: '加大踝关节活动范围，充分拉伸腓肠肌', met: 4.6 },
      { name: '负重坐姿提踵', level: '中级', description: '增加负重强化比目鱼肌刺激', met: 4.7 },
      { name: '器械站姿提踵', level: '中级', description: '稳定负重，双侧小腿均衡训练', met: 4.9 },
      { name: '台阶慢速提踵', level: '中高级', description: '强调离心控制，提升小腿耐力', met: 5.1 },
      { name: '单腿站立提踵', level: '中级', description: '单侧发力，改善左右肌力差距', met: 5.3 },
      { name: '驴式提踵', level: '中高级', description: '躯干前倾，深度拉长腓肠肌', met: 5.7 },
      { name: '单腿器械提踵', level: '中高级', description: '单侧负重，高强度孤立小腿三头肌', met: 6.0 }
    ]
  },
  {
    key: 'forearms',
    label: '前臂',
    color: '#f59e0b',
    exercises: [
      { name: '锤式弯举', level: '中级', description: '侧重肱肌、肱桡肌与前臂，增厚手臂维度', met: 5.1 },
      { name: '窄握杠铃弯举', level: '中高级', description: '窄握距强化前臂桡侧发力', met: 5.4 },
      { name: '正握腕弯举', level: '入门', description: '前臂置于大腿，手腕向上屈伸，强化腕屈肌', met: 3.2 },
      { name: '反握腕弯举', level: '入门 - 中级', description: '手腕向下屈伸，训练腕伸肌与前臂外侧', met: 3.5 },
      { name: '农夫行走', level: '中级', description: '双手负重行走，全面提升握力与前臂耐力', met: 5.8 },
      { name: '毛巾悬挂', level: '入门', description: '双手抓毛巾悬挂，强化指屈肌与握力', met: 3.8 },
      { name: '弹力带腕屈伸', level: '入门', description: '弹力带提供阻力，多角度训练前臂', met: 3.0 },
      { name: '杠铃腕弯举', level: '中级', description: '经典前臂训练，强化腕屈肌群', met: 4.2 }
    ]
  },
  {
    key: 'hip-flexors',
    label: '髋屈肌',
    color: '#8b5cf6',
    exercises: [
      { name: '髋关节铰链', level: '中级', description: '以髋为轴前倾后伸，激活髋屈肌与臀腿', met: 4.8 },
      { name: '站姿提膝', level: '入门', description: '站立交替提膝至髋部高度，激活髋屈肌', met: 3.4 },
      { name: '坐姿髋屈训练', level: '入门 - 中级', description: '坐姿抬膝对抗阻力，孤立训练髋屈肌', met: 3.9 },
      { name: '单腿悬垂举腿', level: '高级', description: '单腿悬垂举腿，更高强度刺激髋屈肌', met: 6.0 },
      { name: '仰卧抬腿', level: '入门 - 中级', description: '仰卧直腿抬起，训练髋屈肌与下腹协同', met: 4.8 },
      { name: '空中蹬车', level: '中级', description: '仰卧模拟蹬车，髋屈肌持续交替收缩', met: 5.8 },
      { name: '仰卧举腿', level: '中级', description: '仰卧举腿至垂直，强化髋屈肌与核心控制', met: 6.3 },
      { name: '悬垂举腿', level: '中高级', description: '悬垂举腿，髋屈肌与核心大幅参与', met: 6.9 }
    ]
  },
  {
    key: 'serratus',
    label: '前锯肌',
    color: '#14b8a6',
    exercises: [
      { name: '肩胛俯卧撑', level: '入门', description: '俯卧撑姿势，仅做肩胛骨前伸后缩，激活前锯肌', met: 3.0 },
      { name: '直臂前推', level: '入门', description: '手臂伸直前推肩胛，训练前锯肌前伸功能', met: 3.2 },
      { name: '宽距俯卧撑（肩胛强化）', level: '中级', description: '宽距俯卧撑，肩胛充分前伸，重点刺激前锯肌', met: 8.2 },
      { name: '绳索肩胛前推', level: '入门 - 中级', description: '双手持绳索，伸直手臂向前推肩胛', met: 3.8 },
      { name: '上斜肩胛推举', level: '中级', description: '上斜推举末段肩胛前伸，强化前锯肌', met: 4.5 },
      { name: '墙壁滑行', level: '入门', description: '背贴墙双臂上滑，肩胛上回旋，改善翼状肩胛', met: 2.8 },
      { name: '前锯肌前伸（弹力带）', level: '入门 - 中级', description: '弹力带抗阻，直臂前伸肩胛', met: 3.5 },
      { name: '单臂肩胛俯卧撑', level: '中高级', description: '单臂支撑肩胛前伸，更高强度刺激前锯肌', met: 5.0 }
    ]
  }
]

export const getLevelColor = (level: TrainingExercise['level']): string => {
  const map: Record<TrainingExercise['level'], string> = {
    '入门': '#43b086',
    '入门 - 中级': '#60a5fa',
    '中级': '#fbbf24',
    '中高级': '#ff8a65',
    '高级': '#ef4444'
  }
  return map[level]
}

export const getMetLevel = (met: number): { label: string; color: string } => {
  if (met < 4) return { label: '轻松', color: '#43b086' }
  if (met < 6) return { label: '中等', color: '#60a5fa' }
  if (met < 8) return { label: '高强度', color: '#fbbf24' }
  return { label: '极高强度', color: '#ef4444' }
}
