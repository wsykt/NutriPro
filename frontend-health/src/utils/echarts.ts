/**
 * ECharts 按需引入（打包体积优化）
 *
 * 原实现直接 import * as echarts from 'echarts'（全量约 1MB min），
 * 现按需注册当前项目实际使用的图表与组件。新增图表类型时在此补充：
 *   - 折线/柱状：LineChart / BarChart（来自 'echarts/charts'）
 *   - 坐标轴：GridComponent / DataZoomComponent（来自 'echarts/components'）
 */
import * as echarts from 'echarts/core'
import { PieChart } from 'echarts/charts'
import {
  TooltipComponent,
  LegendComponent,
  ToolboxComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  PieChart,
  TooltipComponent,
  LegendComponent,
  ToolboxComponent,
  CanvasRenderer,
])

export default echarts
export type { ECharts, EChartsType } from 'echarts/core'
