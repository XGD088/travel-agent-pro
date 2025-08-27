// Travel Agent Pro - Main Content Component
// 主内容区组件

import React from 'react'
import { TripPlanView } from '../trip/TripPlanView'
import { EmptyState } from '../trip/EmptyState'
import { useTripPlan } from '../../stores/tripStore'

export function MainContent() {
  const tripPlan = useTripPlan()
  const hasPlan = !!tripPlan

  return (
    <main className="w-2/3 lg:w-3/4 p-8 lg:p-12">
      <div id="main-content-container">
        {hasPlan ? <TripPlanView /> : <EmptyState />}
      </div>
    </main>
  )
}
