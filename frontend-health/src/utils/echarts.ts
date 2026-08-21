/**
 * ECharts 按需引入 + vue-echarts 组件封装
 *
 * 1. echarts/core 按需注册图表/组件（打包体积优化）
 * 2. 同时导出 VChart 组件（vue-echarts 的 <v-chart />），无需手动 init/dispose/resize
 * 3. 保留 echarts default 导出供底层 setOption / graphic 等静态 API 使用
 */
import * as echarts from 'echarts/core'
import { PieChart, LineChart } from 'echarts/charts'
import {
  TooltipComponent,
  LegendComponent,
  ToolboxComponent,
  GridComponent,
  TitleComponent,
  MarkPointComponent,
  MarkLineComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { use } from 'echarts/core'
import VChart from 'vue-echarts'

use([
  PieChart,
  LineChart,
  TooltipComponent,
  LegendComponent,
  ToolboxComponent,
  GridComponent,
  TitleComponent,
  MarkPointComponent,
  MarkLineComponent,
  CanvasRenderer,
])

export default echarts
export { VChart }
export type { ECharts, EChartsType, ComposeOption } from 'echarts/core'
