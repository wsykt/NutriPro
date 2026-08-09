export interface ExerciseStep {
  title: string
  description: string
}

export interface ExerciseDetail {
  id: number
  name: string
  met: number
  difficulty: '初级' | '中级' | '高级'
  muscleGroup: string
  category: string
  equipment: string
  steps: ExerciseStep[]
  tips: string[]
}

export const EXERCISE_CATEGORIES: Record<string, string> = {
  chest: '胸部', shoulder: '肩部', deltoid: '肩部',
  biceps: '手臂', triceps: '手臂', forearm: '手臂',
  abs: '腹部', obliques: '腹部', serratus: '腹部',
  lats: '背部', traps: '背部', lower: '背部',
  gluteus: '臀部', quads: '大腿', adductors: '大腿', hamstrings: '大腿',
  calves: '小腿', tibialis: '小腿', hip: '臀部'
}

export const EXERCISES: ExerciseDetail[] = [
  {
    id: 1, name: '卧推', met: 7.5, difficulty: '高级', muscleGroup: 'chest', category: '胸部', equipment: '杠铃/哑铃 + 卧推架',
    steps: [
      { title: '准备姿势', description: '平躺在卧推凳上，双脚踩稳地面，双手握杠与肩同宽' },
      { title: '下放杠铃', description: '吸气，缓慢将杠铃下放至胸部上方2-3cm处' },
      { title: '推起杠铃', description: '呼气，用胸部力量将杠铃推起至起始位置' },
      { title: '保持控制', description: '推起时不要完全锁定肘关节，保持肌肉张力' }
    ],
    tips: ['建议使用保护杠', '注意杠铃轨迹接近胸部但不触碰', '保持核心收紧，不要弓背']
  },
  {
    id: 2, name: '上斜卧推', met: 7.0, difficulty: '中级', muscleGroup: 'chest', category: '胸部', equipment: '哑铃 + 上斜凳',
    steps: [
      { title: '调整凳角度', description: '将卧推凳调至20-30度倾斜' },
      { title: '准备姿势', description: '坐在凳上，双手持哑铃于胸前两侧' },
      { title: '推起哑铃', description: '呼气，将哑铃向上推起至手臂伸直' },
      { title: '下放哑铃', description: '吸气，缓慢回到起始位置' }
    ],
    tips: ['主要刺激上胸肌', '避免哑铃在最高点碰撞', '全程控制，不要借力']
  },
  {
    id: 3, name: '俯卧撑', met: 8.0, difficulty: '中级', muscleGroup: 'chest', category: '胸部', equipment: '无',
    steps: [
      { title: '准备姿势', description: '双手撑地与肩同宽，身体成一条直线' },
      { title: '下放身体', description: '吸气，弯曲肘关节将身体下放至胸部接近地面' },
      { title: '推起身体', description: '呼气，伸直手臂将身体推回起始位置' },
      { title: '保持核心', description: '全程保持身体成直线，不要塌腰或翘臀' }
    ],
    tips: ['可从膝盖跪地版开始练习', '保持呼吸节奏', '注意下放深度']
  },
  {
    id: 4, name: '哑铃飞鸟', met: 5.0, difficulty: '初级', muscleGroup: 'chest', category: '胸部', equipment: '哑铃 + 卧推凳',
    steps: [
      { title: '准备姿势', description: '平躺在卧推凳上，双手持哑铃掌心相对' },
      { title: '打开手臂', description: '吸气，弯曲手肘将哑铃向两侧打开至胸部有拉伸感' },
      { title: '合拢哑铃', description: '呼气，将哑铃合拢回到起始位置' }
    ],
    tips: ['保持手肘微屈', '感受胸部拉伸与收缩', '动作要慢要稳']
  },
  {
    id: 5, name: '双杠臂屈伸', met: 8.0, difficulty: '高级', muscleGroup: 'chest', category: '胸部', equipment: '双杠',
    steps: [
      { title: '准备姿势', description: '双臂伸直支撑在双杠上，身体微微前倾' },
      { title: '下放身体', description: '吸气，弯曲手臂将身体下放至手肘呈90度' },
      { title: '推起身体', description: '呼气，伸直手臂将身体推回起始位置' }
    ],
    tips: ['身体前倾刺激胸部，直立刺激三头', '可用弹力带辅助', '控制下放速度']
  },
  {
    id: 6, name: '下斜卧推', met: 7.5, difficulty: '中级', muscleGroup: 'chest', category: '胸部', equipment: '杠铃 + 下斜凳',
    steps: [
      { title: '调整凳角度', description: '将卧推凳调至15-30度下倾' },
      { title: '准备姿势', description: '头高脚低躺在凳上，双手握杠' },
      { title: '下放杠铃', description: '吸气，将杠铃下放至下胸部' },
      { title: '推起杠铃', description: '呼气，将杠铃推回起始位置' }
    ],
    tips: ['主要刺激下胸肌', '注意固定身体', '使用较低重量']
  },
  {
    id: 7, name: '哑铃推举', met: 6.5, difficulty: '中级', muscleGroup: 'shoulder', category: '肩部', equipment: '哑铃 + 椅子',
    steps: [
      { title: '准备姿势', description: '坐在椅子上，双手持哑铃于肩部两侧' },
      { title: '推起哑铃', description: '呼气，将哑铃向上推起至手臂伸直' },
      { title: '下放哑铃', description: '吸气，将哑铃放回肩部位置' }
    ],
    tips: ['不要完全锁定肘关节', '保持核心收紧', '可交替或同时推起']
  },
  {
    id: 8, name: '侧平举', met: 4.0, difficulty: '初级', muscleGroup: 'shoulder', category: '肩部', equipment: '哑铃',
    steps: [
      { title: '准备姿势', description: '站立或坐姿，双手持哑铃于身体两侧' },
      { title: '抬起哑铃', description: '呼气，向两侧抬起哑铃至与地面平行' },
      { title: '放下哑铃', description: '吸气，缓慢回到起始位置' }
    ],
    tips: ['手肘微屈', '不要耸肩', '使用小重量，控制动作']
  },
  {
    id: 9, name: '俯身飞鸟', met: 4.5, difficulty: '初级', muscleGroup: 'deltoid', category: '肩部', equipment: '哑铃 + 凳',
    steps: [
      { title: '准备姿势', description: '俯身，双手持哑铃掌心相对' },
      { title: '抬起哑铃', description: '呼气，向两侧抬起哑铃至与地面平行' },
      { title: '放下哑铃', description: '吸气，缓慢回到起始位置' }
    ],
    tips: ['保持背部平直', '感受后三角肌收缩', '小重量为宜']
  },
  {
    id: 10, name: '阿诺德推举', met: 6.0, difficulty: '中级', muscleGroup: 'shoulder', category: '肩部', equipment: '哑铃',
    steps: [
      { title: '准备姿势', description: '坐姿，双手持哑铃掌心朝向身体' },
      { title: '翻转推起', description: '呼气，同时翻转掌心并将哑铃推起至头顶' },
      { title: '翻转下放', description: '吸气，翻转掌心回到起始位置' }
    ],
    tips: ['动作连贯流畅', '翻转与推起同时进行', '全程控制']
  },
  {
    id: 11, name: '面拉', met: 4.5, difficulty: '初级', muscleGroup: 'deltoid', category: '肩部', equipment: '绳索 + 高位滑轮',
    steps: [
      { title: '准备姿势', description: '面向绳索，双手握绳端，与脸同高' },
      { title: '拉向脸部', description: '呼气，将绳索拉向脸部两侧，手肘向外' },
      { title: '回到起始', description: '吸气，缓慢回到起始位置' }
    ],
    tips: ['手肘保持高位', '感受后三角肌收缩', '控制绳索轨迹']
  },
  {
    id: 12, name: '直立划船', met: 5.5, difficulty: '中级', muscleGroup: 'shoulder', category: '肩部', equipment: '杠铃/哑铃',
    steps: [
      { title: '准备姿势', description: '站立，双手握杠于身前' },
      { title: '向上提拉', description: '呼气，将杠铃沿身体向上提至下巴位置' },
      { title: '下放杠铃', description: '吸气，缓慢回到起始位置' }
    ],
    tips: ['保持杠铃贴近身体', '手肘向外', '避免耸肩']
  },
  {
    id: 13, name: '杠铃弯举', met: 5.5, difficulty: '中级', muscleGroup: 'biceps', category: '手臂', equipment: '杠铃',
    steps: [
      { title: '准备姿势', description: '站立，双手握杠于身前，掌心向上' },
      { title: '弯举杠铃', description: '呼气，弯曲手臂将杠铃弯举至肩部' },
      { title: '下放杠铃', description: '吸气，缓慢回到起始位置' }
    ],
    tips: ['上臂保持不动', '不要借力摆动身体', '全程控制']
  },
  {
    id: 14, name: '锤式弯举', met: 4.5, difficulty: '初级', muscleGroup: 'biceps', category: '手臂', equipment: '哑铃',
    steps: [
      { title: '准备姿势', description: '站立，双手持哑铃掌心相对' },
      { title: '弯举哑铃', description: '呼气，保持掌心相对将哑铃弯举至肩部' },
      { title: '下放哑铃', description: '吸气，缓慢回到起始位置' }
    ],
    tips: ['刺激肱肌和前臂', '上臂固定', '动作缓慢']
  },
  {
    id: 15, name: '集中弯举', met: 5.0, difficulty: '初级', muscleGroup: 'biceps', category: '手臂', equipment: '哑铃 + 凳',
    steps: [
      { title: '准备姿势', description: '坐姿，一手持哑铃，手肘靠在大腿内侧' },
      { title: '弯举哑铃', description: '呼气，弯曲手臂将哑铃弯举至肩部' },
      { title: '下放哑铃', description: '吸气，缓慢回到起始位置' }
    ],
    tips: ['单手训练', '手肘固定', '更集中刺激']
  },
  {
    id: 16, name: '窄距卧推', met: 6.5, difficulty: '中级', muscleGroup: 'triceps', category: '手臂', equipment: '杠铃 + 卧推架',
    steps: [
      { title: '准备姿势', description: '平躺在卧推凳上，双手握距约肩宽一半' },
      { title: '下放杠铃', description: '吸气，将杠铃下放至胸部中央' },
      { title: '推起杠铃', description: '呼气，伸直手臂推起杠铃' }
    ],
    tips: ['主要刺激肱三头肌', '保持手肘贴近身体', '使用标准卧推动作']
  },
  {
    id: 17, name: '绳索下压', met: 5.0, difficulty: '初级', muscleGroup: 'triceps', category: '手臂', equipment: '绳索 + 低位滑轮',
    steps: [
      { title: '准备姿势', description: '面向器械，双手握绳端' },
      { title: '向下压绳', description: '呼气，伸直手臂将绳索向下压' },
      { title: '回到起始', description: '吸气，弯曲手臂回到起始位置' }
    ],
    tips: ['上臂固定', '感受三头肌收缩', '可用V把手或直杆']
  },
  {
    id: 18, name: '仰卧臂屈伸', met: 6.0, difficulty: '中级', muscleGroup: 'triceps', category: '手臂', equipment: '杠铃 + 卧推凳',
    steps: [
      { title: '准备姿势', description: '平躺，双手握杠于胸前，掌心向上' },
      { title: '下放杠铃', description: '吸气，将杠铃向后脑方向下放' },
      { title: '推起杠铃', description: '呼气，伸直手臂将杠铃推回起始位置' }
    ],
    tips: ['上臂保持不动', '仅肘关节运动', '小心控制重量']
  },
  {
    id: 22, name: '仰卧起坐', met: 5.0, difficulty: '初级', muscleGroup: 'abs', category: '腹部', equipment: '垫',
    steps: [
      { title: '准备姿势', description: '躺在垫上，膝盖弯曲，双手抱头' },
      { title: '坐起', description: '呼气，用腹部力量将身体坐起至手肘触碰膝盖' },
      { title: '躺下', description: '吸气，缓慢回到起始位置' }
    ],
    tips: ['不要用手拉头', '用腹部力量起身', '全程控制']
  },
  {
    id: 23, name: '卷腹', met: 4.5, difficulty: '初级', muscleGroup: 'abs', category: '腹部', equipment: '垫',
    steps: [
      { title: '准备姿势', description: '躺在垫上，膝盖弯曲，双手抱头' },
      { title: '抬起上背', description: '呼气，用腹部力量将上背部抬起' },
      { title: '回到地面', description: '吸气，缓慢回到起始位置' }
    ],
    tips: ['下背不离开地面', '感受腹部收缩', '动作范围不必很大']
  },
  {
    id: 26, name: '平板支撑', met: 4.0, difficulty: '初级', muscleGroup: 'abs', category: '腹部', equipment: '垫',
    steps: [
      { title: '准备姿势', description: '前臂撑地，身体成一条直线' },
      { title: '保持姿势', description: '全程收紧核心，保持身体稳定' },
      { title: '结束', description: '达到目标时间后缓慢放下' }
    ],
    tips: ['不要塌腰或翘臀', '深呼吸保持', '循序渐进增加时间']
  },
  {
    id: 32, name: '引体向上', met: 9.0, difficulty: '高级', muscleGroup: 'lats', category: '背部', equipment: '单杠',
    steps: [
      { title: '准备姿势', description: '双手握杠，身体自然下垂' },
      { title: '向上拉', description: '呼气，用背部力量将身体向上拉至胸部接近杠' },
      { title: '放下身体', description: '吸气，缓慢回到起始位置' }
    ],
    tips: ['使用助力带或弹力带辅助', '感受背阔肌收缩', '全程控制不要借力']
  },
  {
    id: 33, name: '高位下拉', met: 7.0, difficulty: '中级', muscleGroup: 'lats', category: '背部', equipment: '拉力器',
    steps: [
      { title: '准备姿势', description: '坐在器械上，双手握横杆' },
      { title: '向下拉', description: '呼气，将横杆下拉至胸部位置' },
      { title: '回到起始', description: '吸气，缓慢回到起始位置' }
    ],
    tips: ['挺胸收腹', '感受背阔肌收缩', '不要后仰太多']
  },
  {
    id: 34, name: '单臂划船', met: 6.0, difficulty: '中级', muscleGroup: 'lats', category: '背部', equipment: '哑铃 + 凳',
    steps: [
      { title: '准备姿势', description: '单膝单手撑凳，另一手持哑铃' },
      { title: '向上拉', description: '呼气，将哑铃向身体方向拉起' },
      { title: '放下哑铃', description: '吸气，缓慢回到起始位置' }
    ],
    tips: ['保持背部平直', '感受背部收缩', '两侧交替']
  },
  {
    id: 36, name: '杠铃划船', met: 6.5, difficulty: '中级', muscleGroup: 'traps', category: '背部', equipment: '杠铃',
    steps: [
      { title: '准备姿势', description: '俯身，双手握杠，背与地面平行' },
      { title: '向上拉', description: '呼气，将杠铃向腹部拉起' },
      { title: '放下杠铃', description: '吸气，缓慢回到起始位置' }
    ],
    tips: ['保持背部平直', '手肘贴近身体', '不要弓背']
  },
  {
    id: 38, name: '硬拉', met: 8.0, difficulty: '高级', muscleGroup: 'lower', category: '背部', equipment: '杠铃',
    steps: [
      { title: '准备姿势', description: '站在杠前，双手握杠，身体贴近杠铃' },
      { title: '伸膝起立', description: '呼气，伸膝将杠铃沿小腿上拉' },
      { title: '完成硬拉', description: '完全站直，杠铃到髋部位置' },
      { title: '放下杠铃', description: '吸气，屈膝将杠铃放回地面' }
    ],
    tips: ['保持背部中立', '杠铃贴近身体', '使用举重腰带保护']
  },
  {
    id: 41, name: '臀桥', met: 5.0, difficulty: '初级', muscleGroup: 'gluteus', category: '臀部', equipment: '垫',
    steps: [
      { title: '准备姿势', description: '躺在垫上，膝盖弯曲，脚掌踩地' },
      { title: '抬起臀部', description: '呼气，用臀部力量将身体抬起至肩髋膝一条直线' },
      { title: '放下臀部', description: '吸气，缓慢回到起始位置' }
    ],
    tips: ['顶峰收缩1-2秒', '感受臀肌刺激', '可加重量增加难度']
  },
  {
    id: 42, name: '臀推', met: 6.0, difficulty: '中级', muscleGroup: 'gluteus', category: '臀部', equipment: '杠铃 + 凳',
    steps: [
      { title: '准备姿势', description: '上背靠凳，杠铃放髋部' },
      { title: '推起身体', description: '呼气，用臀部力量将身体推起至髋部伸直' },
      { title: '放下身体', description: '吸气，缓慢回到起始位置' }
    ],
    tips: ['臀部完全收紧', '保持上背稳定', '循序渐进增加重量']
  },
  {
    id: 44, name: '深蹲', met: 6.0, difficulty: '中级', muscleGroup: 'quads', category: '大腿', equipment: '杠铃 + 深蹲架',
    steps: [
      { title: '准备姿势', description: '杠铃放肩上，双脚与肩同宽' },
      { title: '下蹲', description: '吸气，屈膝下蹲至大腿与地面平行' },
      { title: '起立', description: '呼气，用腿部力量站起至起始位置' }
    ],
    tips: ['膝盖指向脚尖', '保持躯干正直', '可用深蹲架保护']
  },
  {
    id: 45, name: '弓步蹲', met: 5.5, difficulty: '初级', muscleGroup: 'quads', category: '大腿', equipment: '哑铃',
    steps: [
      { title: '准备姿势', description: '站立，双手持哑铃' },
      { title: '前跨步', description: '吸气，向前跨步至前膝弯曲90度' },
      { title: '站回', description: '呼气，用前腿力量站回起始位置' }
    ],
    tips: ['膝盖不超过脚尖', '躯干保持正直', '两侧交替训练']
  },
  {
    id: 46, name: '腿举', met: 7.0, difficulty: '中级', muscleGroup: 'quads', category: '大腿', equipment: '腿举机',
    steps: [
      { title: '准备姿势', description: '坐在器械上，双脚与肩同宽' },
      { title: '推起平台', description: '呼气，用腿部力量将平台推起' },
      { title: '放下平台', description: '吸气，缓慢放下至大腿弯曲90度' }
    ],
    tips: ['不要完全锁定膝关节', '全程控制', '感受腿部收缩']
  },
  {
    id: 50, name: '腿弯举', met: 5.0, difficulty: '初级', muscleGroup: 'hamstrings', category: '大腿', equipment: '腿弯举机',
    steps: [
      { title: '准备姿势', description: '俯卧在器械上，脚踝固定' },
      { title: '向上抬腿', description: '呼气，用腘绳肌将小腿向上弯起' },
      { title: '放下小腿', description: '吸气，缓慢回到起始位置' }
    ],
    tips: ['感受腘绳肌收缩', '不要借助惯性', '控制动作速度']
  },
  {
    id: 52, name: '罗马尼亚硬拉', met: 7.0, difficulty: '中级', muscleGroup: 'hamstrings', category: '大腿', equipment: '杠铃',
    steps: [
      { title: '准备姿势', description: '站立，双手握杠于身前' },
      { title: '下放杠铃', description: '吸气，髋部后推，将杠铃沿小腿前侧下放' },
      { title: '起立', description: '呼气，用腘绳肌和臀部力量站回' }
    ],
    tips: ['膝盖微屈', '感受腘绳肌拉伸', '使用较轻重量']
  },
  {
    id: 53, name: '站姿提踵', met: 5.0, difficulty: '初级', muscleGroup: 'calves', category: '小腿', equipment: '哑铃/杠铃',
    steps: [
      { title: '准备姿势', description: '站立，前脚掌踩在踏板边缘' },
      { title: '抬起脚跟', description: '呼气，踮起脚尖至最高点' },
      { title: '放下脚跟', description: '吸气，缓慢回到起始位置以下' }
    ],
    tips: ['顶峰收缩', '全程控制', '可单腿训练增加难度']
  }
]

export function getExerciseById(id: number): ExerciseDetail | undefined {
  return EXERCISES.find(e => e.id === id)
}

export function getExercisesByMuscle(muscleGroup: string): ExerciseDetail[] {
  return EXERCISES.filter(e => e.muscleGroup === muscleGroup)
}

export function getExercisesByCategory(category: string): ExerciseDetail[] {
  return EXERCISES.filter(e => e.category === category)
}

export const MUSCLE_CATEGORIES = ['胸部', '肩部', '手臂', '腹部', '背部', '臀部', '大腿', '小腿'] as const
export type MuscleCategory = typeof MUSCLE_CATEGORIES[number]

export const CROWD_TYPES = ['普通人群', '健身人群', '青少年', '孕妇', '老年人', '糖尿病患者'] as const
