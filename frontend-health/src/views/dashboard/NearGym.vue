<template>
  <div class="page-fade">
    <h2 class="text-2xl font-bold mb-2 text-morandi-text">附近健身场馆</h2>
    <p class="text-morandi-lightText mb-6 text-sm">以厦门大学嘉庚学院为中心，搜索附近的健身场馆。</p>

    <div class="glass rounded-2xl p-6 mb-6">
      <h3 class="font-semibold mb-4">搜索附近健身馆</h3>
      <div class="flex flex-col sm:flex-row gap-3">
        <input
          v-model="keyword"
          @keyup.enter="handleSearch"
          class="flex-1 px-4 py-3 rounded-xl bg-white/70 border border-morandi-soft text-sm focus:outline-none focus:border-morandi-accent transition-colors"
          placeholder="搜索关键词（如健身房、健身工作室、舞蹈室"
        />
        <button
          @click="handleSearch"
          :disabled="loading"
          class="px-5 py-3 rounded-xl bg-morandi-accent text-white text-sm hover:opacity-90 disabled:opacity-60"
        >
          {{ loading ? '搜索中...' : '搜索' }}
        </button>
      </div>
      <div v-if="userPosition" class="mt-3 text-sm text-morandi-lightText leading-relaxed">
        <div>📍 中心位置：经度 {{ userPosition.lng.toFixed(5) }}，纬度 {{ userPosition.lat.toFixed(5) }}</div>
        <div v-if="locationInfo" class="text-morandi-accent">📌 {{ locationInfo }}</div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 glass rounded-2xl overflow-hidden relative" style="min-height: 560px;">
        <div id="amap-container" class="w-full" style="height: 560px;"></div>
        <div v-if="mapError" class="absolute top-4 left-4 right-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl px-4 py-3 shadow-sm">
          <div class="font-semibold mb-1">地图加载失败</div>
          <div>{{ mapError }}</div>
        </div>
        <div v-if="!mapReady && !mapError" class="absolute inset-0 flex items-center justify-center bg-morandi-gray/60">
          <div class="text-morandi-lightText text-sm">地图正在加载...</div>
        </div>
      </div>
      <div class="glass rounded-2xl p-5" style="max-height: 560px; overflow-y: auto;">
        <h3 class="font-semibold mb-3 text-morandi-text">
          {{ userPosition ? '附近健身馆' : '搜索结果' }}
          <span v-if="pois.length" class="text-xs text-morandi-lightText font-normal ml-1">（{{ pois.length }} 个）</span>
        </h3>
        <div v-if="pois.length === 0 && !loading" class="text-sm text-morandi-lightText py-6 text-center">
          暂无结果，请输入关键字搜索附近健身馆
        </div>
        <div v-if="loading" class="text-sm text-morandi-lightText py-6 text-center">搜索中...</div>
        <div
          v-for="(poi, idx) in pois"
          :key="poi.id || idx"
          class="mb-3 p-3 rounded-xl bg-white/60 hover:bg-morandi-accent/10 cursor-pointer transition-colors"
          @click="focusPoi(poi)"
        >
          <div class="font-semibold text-sm text-morandi-text mb-1">{{ idx + 1 }}. {{ poi.name }}</div>
          <div v-if="poi.address" class="text-xs text-morandi-lightText mb-1">{{ poi.address }}</div>
          <div v-if="poi.tel" class="text-xs text-morandi-lightText mb-1">📞 {{ poi.tel }}</div>
          <div v-if="poi.distance != null && poi.distance !== undefined" class="text-xs text-emerald-600 font-medium">
            距离约 {{ formatDistance(poi.distance) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const keyword = ref('')
const mapReady = ref(false)
const loading = ref(false)
const mapError = ref('')
const pois = ref<any[]>([])

let mapInstance: any = null
let placeSearch: any = null
let geocoder: any = null
let markers: any[] = []
const userPosition = ref<any>(null)
const locationInfo = ref('')
let userMarker: any = null
let userCircle: any = null

function loadAMap(): Promise<any> {
  return new Promise((resolve, reject) => {
    if ((window as any).AMap) {
      resolve((window as any).AMap)
      return
    }
    const existing = document.getElementById('amap-jsapi-script')
    if (existing) {
      const check = setInterval(() => {
        if ((window as any).AMap) {
          clearInterval(check)
          resolve((window as any).AMap)
        }
      }, 100)
      setTimeout(() => {
        if (!(window as any).AMap) {
          clearInterval(check)
          reject(new Error('高德地图 SDK 加载超时'))
        }
      }, 20000)
      return
    }
    if (!(window as any)._AMapSecurityConfig) {
      (window as any)._AMapSecurityConfig = {
        securityJsCode: import.meta.env.VITE_AMAP_SECURITY_KEY
      }
    }
    const AMAP_KEY = import.meta.env.VITE_AMAP_KEY
    const AMAP_SCODE = import.meta.env.VITE_AMAP_SECURITY_KEY
    const plugins = 'AMap.PlaceSearch,AMap.Scale,AMap.ToolBar,AMap.Geocoder'

    const url = 'https://webapi.amap.com/maps?callback=___onAPILoaded&v=2.0&key=' + AMAP_KEY + '&sCode=' + AMAP_SCODE + '&plugin=' + plugins

    ;(window as any).___onAPILoaded = function (err: any) {
      delete (window as any).___onAPILoaded
      if (err) {
        reject(new Error('高德地图返回错误：' + (typeof err === 'string' ? err : err?.message || JSON.stringify(err))))
      } else if ((window as any).AMap) {
        resolve((window as any).AMap)
      } else {
        reject(new Error('高德地图SDK已加载但AMap对象未定义'))
      }
    }
    const script = document.createElement('script')
    script.id = 'amap-jsapi-script'
    script.type = 'text/javascript'
    script.src = url
    script.async = true
    script.onerror = () => {
      reject(new Error('高德地图SDK脚本加载失败，请检查网络或key/安全密钥配置'))
    }
    setTimeout(() => {
      if (!(window as any).AMap) {
        reject(new Error('高德地图SDK加载超时（15秒）'))
      }
    }, 15000)
    document.head.appendChild(script)
  })
}

async function initMap() {
  try {
    const AMap = await loadAMap()
    const searcher = new AMap.PlaceSearch({ pageSize: 1, pageIndex: 1, extensions: 'base', city: '全国' })
    searcher.search('厦门大学嘉庚学院', (status: string, r: any) => {
      let lng = 117.942
      let lat = 24.485
      let name = '厦门大学嘉庚学院'
      if (status === 'complete' && r && r.poiList && r.poiList.pois && r.poiList.pois.length > 0) {
        lng = r.poiList.pois[0].location.lng
        lat = r.poiList.pois[0].location.lat
        if (r.poiList.pois[0].name) {
          name = r.poiList.pois[0].name
        }
      }
      mapInstance = new AMap.Map('amap-container', {
        zoom: 15,
        center: [lng, lat],
        viewMode: '2D'
      })
      try {
        mapInstance.addControl(new AMap.Scale())
        mapInstance.addControl(new AMap.ToolBar({ position: 'RB', offset: new AMap.Pixel(20, 80) }))
      } catch (e) {}
      geocoder = new AMap.Geocoder({ city: '全国' })
      mapInstance.on('complete', () => {
        mapReady.value = true
        userPosition.value = { lng: lng, lat: lat }
        locationInfo.value = name
        drawUserMarker(lng, lat, 500)
        handleSearch()
      })
    })
  } catch (e: any) {
    mapError.value = e?.message || '地图初始化失败'
  }
}

function handleSearch() {
  if (!mapInstance) return
  loading.value = true
  mapError.value = ''
  const AMap = (window as any).AMap
  if (!AMap || !AMap.PlaceSearch) {
    loading.value = false
    mapError.value = '搜索组件未就绪'
    return
  }
  clearPoiMarkers()
  if (userPosition.value) {
    if (!placeSearch) {
      placeSearch = new AMap.PlaceSearch({ pageSize: 20, pageIndex: 1, extensions: 'base' })
    }
    const query = keyword.value.trim() || '健身房'
    const center = [userPosition.value.lng, userPosition.value.lat]
    placeSearch.searchNearBy(query, center, 5000, (status: string, result: any) => {
      loading.value = false
      processSearchResult(status, result)
    })
  } else {
    if (!placeSearch) {
      placeSearch = new AMap.PlaceSearch({ pageSize: 20, pageIndex: 1, city: '全国', extensions: 'base' })
    }
    const query = keyword.value.trim() || '健身房'
    placeSearch.search(query, (status: string, result: any) => {
      loading.value = false
      processSearchResult(status, result)
    })
  }
}

function processSearchResult(status: string, result: any) {
  const AMap = (window as any).AMap
  if (status === 'complete' || status === 'no_data') {
    const list = result?.poiList?.pois || []
    pois.value = list.map((poi: any) => ({
      id: poi.id,
      name: poi.name,
      address: poi.address,
      tel: poi.tel,
      type: poi.type,
      location: poi.location,
      distance: poi.distance
    }))
    if (list.length > 0) {
      list.forEach((poi: any, idx: number) => {
        if (poi.location) {
          const marker = new AMap.Marker({
            position: [poi.location.lng, poi.location.lat],
            title: poi.name,
            map: mapInstance,
            label: {
              content: '<div style="padding:2px 6px;font-size:12px;color:#2d3748;background:rgba(255,255,255,0.9);border-radius:4px;border:1px solid rgba(0,0,0,0.1);">' + (idx + 1) + '. ' + poi.name + '</div>',
              direction: 'top'
            }
          })
          markers.push(marker)
          marker.on('click', () => {
            if (poi.location) {
              mapInstance.setZoomAndCenter(15, [poi.location.lng, poi.location.lat])
            }
          })
        }
      })
      try { mapInstance.setFitView(markers) } catch (e) {}
    }
  } else {
    pois.value = []
    mapError.value = '搜索出错或未找到结果'
  }
}

function clearPoiMarkers() {
  if (markers.length > 0 && mapInstance) {
    try { mapInstance.remove(markers) } catch (e) {}
  }
  markers = []
}

function focusPoi(poi: any) {
  if (!mapInstance || !poi.location) return
  const AMap = (window as any).AMap
  mapInstance.setZoomAndCenter(16, [poi.location.lng, poi.location.lat])
  const info = new AMap.InfoWindow({
    content: '<div style="padding:8px 12px;font-size:12px;"><div style="font-weight:600;margin-bottom:4px;">' + poi.name + '</div>' + (poi.address ? '<div style="color:#718096;">地址：' + poi.address + '</div>' : '') + (poi.tel ? '<div style="color:#718096;">电话：' + poi.tel + '</div>' : '') + '</div>',
    offset: new AMap.Pixel(0, -30)
  })
  info.open(mapInstance, [poi.location.lng, poi.location.lat])
}

function formatDistance(distance: number): string {
  if (distance == null) return ''
  if (distance < 1000) return Math.round(distance) + ' 米'
  return (distance / 1000).toFixed(2) + ' km'
}

function drawUserMarker(lng: number, lat: number, accuracy: number | undefined) {
  const AMap = (window as any).AMap
  if (userMarker) { try { mapInstance.remove(userMarker) } catch (e) {} }
  if (userCircle) { try { mapInstance.remove(userCircle) } catch (e) {} }

  userMarker = new AMap.Marker({
    position: [lng, lat],
    map: mapInstance,
    content: '<div style="width:24px;height:24px;background:#43b086;border:3px solid #fff;border-radius:50%;box-shadow:0 0 8px rgba(0,0,0,0.3);"></div>',
    offset: new AMap.Pixel(-12, -12),
    zIndex: 200
  })
  if (accuracy) {
    userCircle = new AMap.Circle({
      center: [lng, lat],
      radius: accuracy,
      strokeColor: '#43b086',
      strokeWeight: 2,
      strokeOpacity: 0.8,
      fillColor: '#43b086',
      fillOpacity: 0.12,
      map: mapInstance,
      zIndex: 199
    })
  }
}

onMounted(() => {
  userStore.init()
  initMap()
})

onBeforeUnmount(() => {
  clearPoiMarkers()
  if (userMarker) { try { mapInstance.remove(userMarker) } catch (e) {} }
  if (userCircle) { try { mapInstance.remove(userCircle) } catch (e) {} }
  if (mapInstance) {
    try { mapInstance.destroy() } catch (e) {}
    mapInstance = null
  }
  placeSearch = null
  geocoder = null
})
</script>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.9);
}
.page-fade {
  animation: fadeIn 0.3s ease forwards;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
