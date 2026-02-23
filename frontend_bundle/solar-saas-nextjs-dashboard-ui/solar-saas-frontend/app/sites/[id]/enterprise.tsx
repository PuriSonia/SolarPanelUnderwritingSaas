"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { enterpriseApi } from "@/lib/enterprise";
import { Card } from "@/components/Card";
import ForecastChart from "@/components/ForecastChart";
import TrendArrow from "@/components/TrendArrow";

export default function EnterprisePanel() {
  const params = useParams<{ id: string }>();
  const siteId = Number(params.id);
  const year = new Date().getFullYear();

  const [scorecard, setScorecard] = useState<any>(null);
  const [forecast, setForecast] = useState<any>(null);

  useEffect(() => {
    enterpriseApi.siteScorecard(siteId, year).then(setScorecard);
    enterpriseApi.forecast(siteId).then(setForecast);
  }, [siteId, year]);

  return (
    <div className="grid grid-cols-1 gap-6 mt-6">

      <Card title="ESG Scorecard">
        {scorecard && (
          <div className="space-y-2 text-sm">
            <div>Renewable %: <b>{scorecard.renewable_percentage}%</b></div>
            <div>Net Scope 2: <b>{scorecard.net_scope2_tco2e}</b></div>
            <div>Solar Avoided: <b>{scorecard.solar_avoided_tco2e}</b></div>
            <div>YoY Delta: 
              <TrendArrow value={scorecard.yoy?.delta_net_scope2_tco2e || 0} />
            </div>
          </div>
        )}
      </Card>

      <Card title="5-Year Forecast">
        {forecast && (
          <>
            <div className="space-y-2 text-sm mb-4">
              <div>NPV: <b>{forecast.npv}</b></div>
              <div>IRR: <b>{forecast.irr}</b></div>
            </div>
            {forecast.projection && <ForecastChart data={forecast.projection} />}
          </>
        )}
      </Card>

      <Card title="Lender Export">
        <button
          className="px-4 py-2 bg-black text-white rounded"
          onClick={() => window.print()}
        >
          Export PDF (Print)
        </button>
      </Card>

    </div>
  );
}
