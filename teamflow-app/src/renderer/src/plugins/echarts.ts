import {use} from 'echarts/core';
import {CanvasRenderer} from 'echarts/renderers';
import {ScatterChart, LineChart, BarChart, TreeChart} from 'echarts/charts';
import 'echarts-wordcloud'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  ToolboxComponent,
  VisualMapComponent,
  DataZoomComponent,
  GraphicComponent,
} from 'echarts/components';
import VChart from 'vue-echarts'; // Import the vue-echarts component

// Register the required ECharts components
use([
  CanvasRenderer,
  // Charts
  ScatterChart,
  LineChart,
  BarChart,
  TreeChart,
  // Components
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  ToolboxComponent,
  VisualMapComponent,
  DataZoomComponent,
  GraphicComponent
]);

// We will register VChart globally in main.ts
export {VChart};
