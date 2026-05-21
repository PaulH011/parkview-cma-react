'use client';

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, BookOpen, Calculator, TrendingUp, Building2, BarChart3, Target, Table } from 'lucide-react';

export default function MethodologyPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      {/* Header */}
      <div className="mb-8">
        <Link
          href="/"
          className="inline-flex items-center text-sm text-slate-500 hover:text-slate-700 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Dashboard
        </Link>
        <h1 className="text-3xl font-bold text-slate-800 flex items-center gap-3">
          <BookOpen className="h-8 w-8" />
          Methodology Reference Guide
        </h1>
        <p className="text-slate-600 mt-2">
          Complete documentation of the Parkview CMA calculation methodology. Understand how
          expected returns are calculated and what each input assumption means.
        </p>
      </div>

      {/* Quick Navigation */}
      <Card className="mb-8">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">Quick Navigation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 md:grid-cols-5 gap-2 text-sm">
            <a href="#overview" className="text-blue-600 hover:underline">Overview</a>
            <a href="#base-currency" className="text-blue-600 hover:underline">Base Currency & FX</a>
            <a href="#macro-models" className="text-blue-600 hover:underline">Macro Models</a>
            <a href="#liquidity" className="text-blue-600 hover:underline">Liquidity</a>
            <a href="#bonds" className="text-blue-600 hover:underline">Bonds</a>
            <a href="#equity" className="text-blue-600 hover:underline">Equity</a>
            <a href="#absolute-return" className="text-blue-600 hover:underline">Absolute Return</a>
            <a href="#default-assumptions" className="text-blue-600 hover:underline">Default Assumptions</a>
            <a href="#faq" className="text-blue-600 hover:underline">FAQ</a>
          </div>
        </CardContent>
      </Card>

      {/* Overview */}
      <section id="overview" className="mb-12">
        <h2 className="text-2xl font-bold text-slate-800 border-b-2 border-slate-800 pb-2 mb-4">
          Overview
        </h2>
        <div className="prose prose-slate max-w-none">
          <p>
            The Parkview CMA methodology produces <strong>10-year expected returns</strong> for major asset classes.
            The methodology is built on several key principles:
          </p>
          <ol className="list-decimal list-inside space-y-2 my-4">
            <li><strong>Building Block Approach</strong>: Returns are decomposed into fundamental components (yield, growth, valuation changes, etc.)</li>
            <li><strong>Mean Reversion</strong>: Valuations and spreads are assumed to revert to fair value over time</li>
            <li><strong>Forward-Looking Macro</strong>: Economic forecasts drive rate expectations</li>
            <li><strong>Consistency</strong>: All asset classes use the same underlying macro assumptions</li>
          </ol>
        </div>

        <Card className="bg-blue-50 border-blue-200 mt-4">
          <CardContent className="pt-4">
            <h4 className="font-semibold text-blue-800 mb-2">Key Concept: Real vs. Nominal Returns</h4>
            <ul className="text-sm text-blue-700 space-y-1">
              <li><strong>Nominal Return</strong> = What you actually receive (includes inflation)</li>
              <li><strong>Real Return</strong> = Purchasing power gain (excludes inflation)</li>
              <li>Nominal Return = Real Return + Expected Inflation</li>
            </ul>
          </CardContent>
        </Card>

        <Card className="bg-green-50 border-green-200 mt-4">
          <CardContent className="pt-4">
            <h4 className="font-semibold text-green-800 mb-2">Feature: Asset Breakdown</h4>
            <p className="text-sm text-green-700">
              Click on any asset class row in the results table to see a detailed breakdown of the return calculation,
              including the formula, component attribution chart, and input values. Blue badges indicate user overrides.
            </p>
          </CardContent>
        </Card>

        <Card className="bg-purple-50 border-purple-200 mt-4">
          <CardContent className="pt-4">
            <h4 className="font-semibold text-purple-800 mb-2">Feature: Dual Equity Models</h4>
            <p className="text-sm text-purple-700">
              The tool supports two equity models that can be toggled in the Equity input tab:
              the <strong>RA Model</strong> (CAEY-based, produces real returns) and the <strong>Grinold-Kroner Model</strong> (P/E-based,
              produces nominal returns with revenue growth linked to macro). See the <a href="#equity" className="underline">Equity Models</a> section for details.
            </p>
          </CardContent>
        </Card>

        <Card className="bg-blue-50 border-blue-200 mt-4">
          <CardContent className="pt-4">
            <h4 className="font-semibold text-blue-800 mb-2">Feature: EUR FX Explanation</h4>
            <p className="text-sm text-blue-700">
              When EUR is selected as base currency, a dedicated <strong>Currency Adjustment</strong> card appears showing
              the FX methodology, carry/PPP breakdown per currency pair, and the FX impact on each affected asset class.
            </p>
          </CardContent>
        </Card>
      </section>

      {/* Base Currency & FX */}
      <section id="base-currency" className="mb-12">
        <h2 className="text-2xl font-bold text-slate-800 border-b-2 border-slate-800 pb-2 mb-4">
          Base Currency & FX Adjustments
        </h2>
        <p className="mb-4">
          The tool supports two base currencies: <strong>USD</strong> and <strong>EUR</strong>. When you select a base currency,
          all returns are expressed from that currency's perspective, with appropriate FX adjustments applied to foreign assets.
        </p>

        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 font-mono text-sm mb-4">
          <strong>E[FX Return] = 30% × (Home T-Bill - Foreign T-Bill) + 70% × (Home Inflation - Foreign Inflation)</strong>
        </div>

        <p className="mb-4">
          This formula is based on <strong>Purchasing Power Parity (PPP)</strong> theory with two components:
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse mb-4">
            <thead>
              <tr className="bg-slate-800 text-white">
                <th className="p-2 text-left">Component</th>
                <th className="p-2 text-left">Weight</th>
                <th className="p-2 text-left">Formula</th>
                <th className="p-2 text-left">Interpretation</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b">
                <td className="p-2 font-medium">Carry</td>
                <td className="p-2">30%</td>
                <td className="p-2">Home T-Bill - Foreign T-Bill</td>
                <td className="p-2">Short-term interest rate differential</td>
              </tr>
              <tr className="border-b">
                <td className="p-2 font-medium">PPP</td>
                <td className="p-2">70%</td>
                <td className="p-2">Home Inflation - Foreign Inflation</td>
                <td className="p-2">Long-term inflation differential</td>
              </tr>
            </tbody>
          </table>
        </div>

        <Card className="bg-blue-50 border-blue-200 mt-4 mb-6">
          <CardContent className="pt-4">
            <h4 className="font-semibold text-blue-800 mb-2">Visual FX Breakdown (EUR Mode)</h4>
            <p className="text-sm text-blue-700">
              When you toggle to <strong>EUR</strong> as the base currency, a <strong>Currency Adjustment</strong> card
              appears on the dashboard showing the carry and PPP components for each currency pair
              (EUR/USD, EUR/JPY, EUR/EM), which asset classes each pair affects, and the per-asset FX impact.
              Additionally, the asset breakdown waterfall charts will include an <strong>FX Return</strong> bar
              showing the currency adjustment contribution for each non-EUR asset.
            </p>
          </CardContent>
        </Card>

        <h3 className="text-lg font-semibold mt-6 mb-3">Asset Currency Mapping</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-slate-800 text-white">
                <th className="p-2 text-left">Asset Class</th>
                <th className="p-2 text-left">Local Currency</th>
                <th className="p-2 text-left">USD Base</th>
                <th className="p-2 text-left">EUR Base</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b"><td className="p-2">Liquidity</td><td className="p-2">Base currency</td><td className="p-2">No FX adjustment</td><td className="p-2">No FX adjustment</td></tr>
              <tr className="border-b"><td className="p-2">Bonds Global</td><td className="p-2">USD</td><td className="p-2">No FX adjustment</td><td className="p-2">FX adjustment applied</td></tr>
              <tr className="border-b"><td className="p-2">Bonds HY</td><td className="p-2">USD</td><td className="p-2">No FX adjustment</td><td className="p-2">FX adjustment applied</td></tr>
              <tr className="border-b"><td className="p-2">Bonds EM</td><td className="p-2">USD</td><td className="p-2">No FX adjustment</td><td className="p-2">FX adjustment applied</td></tr>
              <tr className="border-b"><td className="p-2">Bonds Inflation Linked</td><td className="p-2">Base currency regime</td><td className="p-2">Uses USD TIPS regime</td><td className="p-2">Uses EUR ILB regime</td></tr>
              <tr className="border-b"><td className="p-2">Equity US</td><td className="p-2">USD</td><td className="p-2">No FX adjustment</td><td className="p-2">FX adjustment applied</td></tr>
              <tr className="border-b"><td className="p-2">Equity Europe</td><td className="p-2">EUR</td><td className="p-2">FX adjustment applied</td><td className="p-2">No FX adjustment</td></tr>
              <tr className="border-b"><td className="p-2">Equity Japan</td><td className="p-2">JPY</td><td className="p-2">FX adjustment applied</td><td className="p-2">FX adjustment applied</td></tr>
              <tr className="border-b"><td className="p-2">Equity EM</td><td className="p-2">EM currencies</td><td className="p-2">FX adjustment applied</td><td className="p-2">FX adjustment applied</td></tr>
              <tr className="border-b"><td className="p-2">Absolute Return</td><td className="p-2">Base currency</td><td className="p-2">No FX adjustment</td><td className="p-2">No FX adjustment</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Macro Models */}
      <section id="macro-models" className="mb-12">
        <h2 className="text-2xl font-bold text-slate-800 border-b-2 border-slate-800 pb-2 mb-4 flex items-center gap-2">
          <Calculator className="h-6 w-6" />
          Macro Economic Models
        </h2>
        <p className="mb-4">
          Macro forecasts are the foundation for all asset class returns. The tool computes forecasts
          for four regions: <strong>US</strong>, <strong>Eurozone</strong>, <strong>Japan</strong>, and <strong>Emerging Markets (EM)</strong>.
        </p>

        <Tabs defaultValue="gdp" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="gdp">GDP Growth</TabsTrigger>
            <TabsTrigger value="inflation">Inflation</TabsTrigger>
            <TabsTrigger value="tbill">T-Bill Rate</TabsTrigger>
          </TabsList>

          <TabsContent value="gdp" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">GDP Growth Model</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 font-mono text-sm mb-4">
                  <strong>E[Real GDP Growth] = E[Output-per-Capita Growth] + E[Population Growth]</strong>
                </div>
                <p className="mb-2">Where Output-per-Capita Growth is computed as:</p>
                <div className="bg-slate-100 border rounded-lg p-4 font-mono text-sm mb-4">
                  E[Output-per-Capita] = Productivity Growth + Demographic Effect + Adjustment
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="bg-slate-100">
                        <th className="p-2 text-left">Component</th>
                        <th className="p-2 text-left">Description</th>
                        <th className="p-2 text-left">How It's Determined</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b"><td className="p-2 font-medium">Population Growth</td><td className="p-2">Expected population growth rate</td><td className="p-2">UN Population Database forecasts</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Productivity Growth</td><td className="p-2">Output per worker growth</td><td className="p-2">EWMA of historical data (5-year half-life)</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Demographic Effect</td><td className="p-2">Impact of aging population</td><td className="p-2">Sigmoid function of MY (Middle/Young) ratio</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Adjustment</td><td className="p-2">Skewness correction</td><td className="p-2">-0.3% (DM) or -0.5% (EM)</td></tr>
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="inflation" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Inflation Model</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 font-mono text-sm mb-4">
                  <strong>E[Inflation] = 30% × Current Headline Inflation + 70% × Long-Term Inflation</strong>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="bg-slate-100">
                        <th className="p-2 text-left">Component</th>
                        <th className="p-2 text-left">Description</th>
                        <th className="p-2 text-left">Default Values</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b"><td className="p-2 font-medium">Current Headline</td><td className="p-2">Latest YoY CPI reading</td><td className="p-2">US: 2.5%, EU: 2.2%, JP: 2.0%, EM: 4.5%</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Long-Term Inflation</td><td className="p-2">Central bank target or EWMA of core</td><td className="p-2">US: 2.2%, EU: 2.0%, JP: 1.5%, EM: 3.5%</td></tr>
                    </tbody>
                  </table>
                </div>
                <p className="text-sm text-slate-600 mt-4">
                  <strong>Why 30/70 Weighting?</strong> Current inflation captures near-term momentum while
                  the long-term anchor represents central bank credibility.
                </p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="tbill" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">T-Bill Rate Model</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 font-mono text-sm mb-4">
                  <strong>E[T-Bill] = 30% × Current T-Bill + 70% × Long-Term T-Bill</strong>
                </div>
                <p className="mb-2">Where the Long-Term T-Bill rate is:</p>
                <div className="bg-slate-100 border rounded-lg p-4 font-mono text-sm mb-4">
                  Long-Term T-Bill = max(-0.75%, Country Factor + E[Real GDP] + E[Inflation])
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="bg-slate-100">
                        <th className="p-2 text-left">Component</th>
                        <th className="p-2 text-left">Description</th>
                        <th className="p-2 text-left">Default Values</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b"><td className="p-2 font-medium">Current T-Bill</td><td className="p-2">Today's 3-month T-Bill rate</td><td className="p-2">US: 3.53%, EU: 1.80%, JP: 1.62%, EM: 4.00%</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Country Factor</td><td className="p-2">Liquidity/risk premium</td><td className="p-2">US: 0%, EU: -0.2%, JP: -0.5%, EM: -3.4%</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Rate Floor</td><td className="p-2">Minimum possible rate</td><td className="p-2">-0.75%</td></tr>
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </section>

      {/* Liquidity */}
      <section id="liquidity" className="mb-12">
        <h2 className="text-2xl font-bold text-slate-800 border-b-2 border-slate-800 pb-2 mb-4">
          Liquidity (Cash/T-Bills)
        </h2>
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 font-mono text-sm mb-4">
          <strong>E[Liquidity Return] = E[T-Bill Rate]</strong>
        </div>
        <p>
          The simplest asset class - cash returns equal the expected average T-Bill rate over the forecast horizon.
          No credit risk, no duration risk. Real return = Nominal return - Inflation.
        </p>
      </section>

      {/* Bonds */}
      <section id="bonds" className="mb-12">
        <h2 className="text-2xl font-bold text-slate-800 border-b-2 border-slate-800 pb-2 mb-4 flex items-center gap-2">
          <Building2 className="h-6 w-6" />
          Bond Models
        </h2>

        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 font-mono text-sm mb-6">
          <strong>E[Bond Return] = Yield Component + Roll Return + Valuation Return - Credit Losses</strong>
        </div>

        <Tabs defaultValue="global" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="global">Bonds Global</TabsTrigger>
            <TabsTrigger value="hy">Bonds High Yield</TabsTrigger>
            <TabsTrigger value="em">Bonds EM</TabsTrigger>
            <TabsTrigger value="inflation-linked">Bonds Inflation Linked</TabsTrigger>
          </TabsList>

          <TabsContent value="global" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Government Bonds (Bonds Global)</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="mb-4">For developed market government bonds, Credit Losses = 0 (assumed default-free).</p>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2">Yield Component</h4>
                    <p className="font-mono text-sm bg-white p-2 rounded mb-2">Avg Yield = E[T-Bill] + Avg Term Premium</p>
                    <p className="text-sm text-slate-600">The yield you earn from holding the bond. Term premium mean-reverts from current to fair value over time.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2">Roll Return</h4>
                    <p className="font-mono text-sm bg-white p-2 rounded mb-2">Roll = (Term Premium / Maturity) × Duration</p>
                    <p className="text-sm text-slate-600">Captures the "roll down" effect as bonds approach maturity.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2">Valuation Return</h4>
                    <p className="font-mono text-sm bg-white p-2 rounded mb-2">Val = -Duration × (ΔTerm Premium / Horizon)</p>
                    <p className="text-sm text-slate-600">Capital gain/loss from yield changes. Rising yields = falling prices.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2">Default Inputs</h4>
                    <ul className="text-sm space-y-1">
                      <li>Current Yield: 3.5%</li>
                      <li>Duration: 7.0 years</li>
                      <li>Current Term Premium: 1.0%</li>
                      <li>Fair Term Premium: 1.5%</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="hy" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">High Yield Bonds</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="mb-4">High yield bonds follow the same framework but include <strong>credit spread</strong> and <strong>credit losses</strong>.</p>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2">Credit Spread Component</h4>
                    <p className="font-mono text-sm bg-white p-2 rounded mb-2">Avg Yield = E[T-Bill] + Term Premium + Credit Spread</p>
                    <p className="text-sm text-slate-600">Credit spread also mean-reverts to fair value.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2">Credit Loss Component</h4>
                    <p className="font-mono text-sm bg-white p-2 rounded mb-2">Credit Loss = Default Rate × (1 - Recovery Rate)</p>
                    <p className="text-sm text-slate-600">Annual expected loss from defaults.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg col-span-2">
                    <h4 className="font-semibold mb-2">Default Inputs</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                      <div>Current Yield: 7.5%</div>
                      <div>Duration: 4.0 years</div>
                      <div>Credit Spread: 2.71%</div>
                      <div>Fair Credit Spread: 4.0%</div>
                      <div>Default Rate: 5.5%</div>
                      <div>Recovery Rate: 40%</div>
                      <div className="font-semibold">Annual Credit Loss: 3.3%</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="em" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">EM Hard Currency Bonds</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="mb-4">
                  EM hard currency bonds are USD-denominated sovereign bonds. Since they are priced off the US Treasury curve,
                  they use <strong>US macro assumptions</strong> (not EM macro).
                </p>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                  <p className="font-mono text-sm mb-2"><strong>Yield = E[US T-Bill] + Term Premium + EM Credit Spread (~2%)</strong></p>
                  <p className="font-mono text-sm"><strong>Real Return = Nominal Return - US Inflation</strong></p>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="bg-slate-100">
                        <th className="p-2 text-left">Input</th>
                        <th className="p-2 text-left">Default</th>
                        <th className="p-2 text-left">Note</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b"><td className="p-2">Current Yield</td><td className="p-2">5.77%</td><td className="p-2">BBG EM USD Aggregate Index YTM</td></tr>
                      <tr className="border-b"><td className="p-2">Duration</td><td className="p-2">5.5 years</td><td className="p-2">Typically shorter than DM</td></tr>
                      <tr className="border-b"><td className="p-2">Default Rate</td><td className="p-2">2.8%</td><td className="p-2">EM hard currency sovereign default rate</td></tr>
                      <tr className="border-b"><td className="p-2">Recovery Rate</td><td className="p-2">55%</td><td className="p-2">Typical EM sovereign recovery</td></tr>
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="inflation-linked" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Bonds Inflation Linked (Regime-Based)</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="mb-4">
                  Inflation-linked bonds switch regime based on base currency:
                  <strong> USD base uses US TIPS</strong>, and <strong>EUR base uses EUR inflation-linked sovereigns</strong>.
                </p>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                  <p className="font-mono text-sm mb-2"><strong>E[Real Return] = Real Carry + Real Roll + Real Valuation + Liquidity/Technical</strong></p>
                  <p className="font-mono text-sm"><strong>E[Nominal Return] = E[Real Return] + Inflation Indexation - Index Lag Drag</strong></p>
                </div>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2">USD (TIPS) Defaults</h4>
                    <ul className="text-sm space-y-1">
                      <li>Current Real Yield: 2.10%</li>
                      <li>Duration: 4.3 years</li>
                      <li>Index Lag Drag: 0.10%</li>
                    </ul>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2">EUR (ILBs) Defaults</h4>
                    <ul className="text-sm space-y-1">
                      <li>Current Real Yield: 0.75%</li>
                      <li>Duration: 7.5 years</li>
                      <li>Index Lag Drag: 0.15%</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </section>

      {/* Equity */}
      <section id="equity" className="mb-12">
        <h2 className="text-2xl font-bold text-slate-800 border-b-2 border-slate-800 pb-2 mb-4 flex items-center gap-2">
          <TrendingUp className="h-6 w-6" />
          Equity Models
        </h2>

        <p className="mb-4 text-slate-600">
          The tool supports <strong>two equity models</strong> that can be toggled in the Equity input panel.
          All four equity regions (US, Europe, Japan, EM) use the same model at any given time.
        </p>

        <Tabs defaultValue="ra-model" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="ra-model">RA Model (CAEY-Based)</TabsTrigger>
            <TabsTrigger value="gk-model">Grinold-Kroner Model (P/E-Based)</TabsTrigger>
          </TabsList>

          {/* RA Model */}
          <TabsContent value="ra-model" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  RA Model
                  <Badge variant="outline" className="bg-slate-100">Default</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 font-mono text-sm mb-4">
                  <strong>E[Real Equity Return] = Dividend Yield + Real EPS Growth + Valuation Change (CAEY)</strong>
                </div>
                <p className="mb-4 text-slate-600">
                  This produces a <strong>real</strong> return. Add regional inflation to get the nominal return.
                </p>

                <div className="grid md:grid-cols-3 gap-4 mb-6">
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2">Dividend Yield</h4>
                    <p className="font-mono text-sm bg-white p-2 rounded mb-2">DY = Current Trailing 12-Month Yield</p>
                    <p className="text-sm text-slate-600">Taken as current value with no mean reversion assumed.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2">Real EPS Growth</h4>
                    <p className="font-mono text-sm bg-white p-2 rounded mb-2">EPS = 50% × Country + 50% × Regional</p>
                    <p className="text-sm text-slate-600">Blended growth capped at Global GDP; 50-year log-linear trend.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2">Valuation Change</h4>
                    <p className="font-mono text-sm bg-white p-2 rounded mb-2">Val = (Fair CAEY / Current CAEY)^(1/20) - 1</p>
                    <p className="text-sm text-slate-600">CAEY (1/CAPE) reverts to fair value over 20 years.</p>
                  </div>
                </div>

                <h4 className="font-semibold mb-3">RA Model Default Inputs</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="bg-slate-800 text-white">
                        <th className="p-2 text-left">Input</th>
                        <th className="p-2 text-right">US</th>
                        <th className="p-2 text-right">Europe</th>
                        <th className="p-2 text-right">Japan</th>
                        <th className="p-2 text-right">EM</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b"><td className="p-2 font-medium">Dividend Yield</td><td className="p-2 text-right">1.10%</td><td className="p-2 text-right">2.80%</td><td className="p-2 text-right">1.90%</td><td className="p-2 text-right">2.20%</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Current CAEY</td><td className="p-2 text-right">2.50%</td><td className="p-2 text-right">4.40%</td><td className="p-2 text-right">3.70%</td><td className="p-2 text-right">3.80%</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Fair CAEY</td><td className="p-2 text-right">4.30%</td><td className="p-2 text-right">4.30%</td><td className="p-2 text-right">3.70%</td><td className="p-2 text-right">5.80%</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Country EPS Growth</td><td className="p-2 text-right">1.80%</td><td className="p-2 text-right">1.20%</td><td className="p-2 text-right">0.80%</td><td className="p-2 text-right">3.00%</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Regional EPS Growth</td><td className="p-2 text-right">1.60%</td><td className="p-2 text-right">1.60%</td><td className="p-2 text-right">1.60%</td><td className="p-2 text-right">2.80%</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Reversion Speed</td><td className="p-2 text-right">100%</td><td className="p-2 text-right">100%</td><td className="p-2 text-right">100%</td><td className="p-2 text-right">100%</td></tr>
                    </tbody>
                  </table>
                </div>

                <Card className="bg-green-50 border-green-200 mt-4">
                  <CardContent className="pt-4">
                    <p className="text-sm text-green-700">
                      <strong>Valuation Impact:</strong> US equities still have a material valuation headwind (Current CAEY 2.50% vs Fair 4.30%),
                      implying CAPE compresses from ~40x toward ~23x over 20 years.
                      Europe and Japan are essentially at fair value (no headwind/tailwind).
                      EM has flipped to a headwind (Current 3.80% vs Fair 5.80% — CAPE ~26x compressing toward ~17x).
                    </p>
                  </CardContent>
                </Card>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Grinold-Kroner Model */}
          <TabsContent value="gk-model" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  Grinold-Kroner Model
                  <Badge variant="outline" className="bg-purple-100 text-purple-700 border-purple-200">Alternative</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 font-mono text-sm mb-4">
                  <strong>E[Nominal Return] = Dividend Yield + Net Buyback Yield + Revenue Growth + Margin Change + Valuation Change (P/E)</strong>
                </div>
                <p className="mb-4 text-slate-600">
                  The GK model produces a <strong>nominal</strong> return directly (no need to add inflation).
                  It decomposes equity returns into five components covering income, growth, and repricing.
                </p>

                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2 text-green-700">Dividend Yield</h4>
                    <p className="font-mono text-sm bg-white p-2 rounded mb-2">DY = Current Trailing 12-Month Yield</p>
                    <p className="text-sm text-slate-600">Income from dividends, taken at current market value.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2 text-emerald-700">Net Buyback Yield</h4>
                    <p className="font-mono text-sm bg-white p-2 rounded mb-2">Buyback = Gross Buybacks - New Issuance</p>
                    <p className="text-sm text-slate-600">Net shareholder yield from buybacks minus dilution from new issuance.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2 text-blue-700">Revenue Growth</h4>
                    <p className="font-mono text-sm bg-white p-2 rounded mb-2">RevGrowth = Inflation + Real GDP + Wedge</p>
                    <p className="text-sm text-slate-600">Auto-computed from regional macro, or directly overridden. See below for details.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2 text-indigo-700">Margin Change</h4>
                    <p className="font-mono text-sm bg-white p-2 rounded mb-2">Margin = Annual profit margin change</p>
                    <p className="text-sm text-slate-600">Positive = expansion (e.g., reform). Negative = compression from peak margins.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2 text-amber-700">Valuation Change</h4>
                    <p className="font-mono text-sm bg-white p-2 rounded mb-2">Val = (Target P/E / Current P/E)^(1/10) - 1</p>
                    <p className="text-sm text-slate-600">P/E convergence to equilibrium over the 10-year forecast horizon.</p>
                  </div>
                </div>

                {/* Macro-Linked Revenue Growth */}
                <Card className="bg-blue-50 border-blue-200 mb-6">
                  <CardContent className="pt-4">
                    <h4 className="font-semibold text-blue-800 mb-2">Macro-Linked Revenue Growth</h4>
                    <p className="text-sm text-blue-700 mb-3">
                      Revenue Growth is the key link between the macro models and the GK equity model.
                      Unless directly overridden by the user, it is <strong>auto-computed</strong> from regional macro forecasts:
                    </p>
                    <div className="bg-white border border-blue-200 rounded-lg p-3 font-mono text-sm mb-3">
                      Revenue Growth = Regional Inflation + Regional Real GDP Growth + Revenue-GDP Wedge
                    </div>
                    <ul className="text-sm text-blue-700 space-y-1">
                      <li><strong>Regional Inflation</strong>: From the macro inflation model (30% current + 70% long-term)</li>
                      <li><strong>Regional Real GDP</strong>: From the macro GDP model (productivity + population + demographics)</li>
                      <li><strong>Revenue-GDP Wedge</strong>: Premium/discount of corporate revenue growth over nominal GDP (e.g., +2% for US due to global revenue exposure)</li>
                    </ul>
                    <p className="text-sm text-blue-700 mt-3">
                      <strong>Override behavior:</strong> If you manually set Revenue Growth in the equity inputs, the macro link is broken
                      and your value is used directly. The computed value is still shown for reference.
                    </p>
                  </CardContent>
                </Card>

                <h4 className="font-semibold mb-3">GK Model Default Inputs</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="bg-slate-800 text-white">
                        <th className="p-2 text-left">Input</th>
                        <th className="p-2 text-right">US</th>
                        <th className="p-2 text-right">Europe</th>
                        <th className="p-2 text-right">Japan</th>
                        <th className="p-2 text-right">EM</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b"><td className="p-2 font-medium">Dividend Yield</td><td className="p-2 text-right">1.10%</td><td className="p-2 text-right">2.80%</td><td className="p-2 text-right">1.90%</td><td className="p-2 text-right">2.20%</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Net Buyback Yield</td><td className="p-2 text-right">1.30%</td><td className="p-2 text-right">0.70%</td><td className="p-2 text-right">1.40%</td><td className="p-2 text-right">-0.60%</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Revenue-GDP Wedge</td><td className="p-2 text-right">2.00%</td><td className="p-2 text-right">0.50%</td><td className="p-2 text-right">0.50%</td><td className="p-2 text-right">0.50%</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Margin Change</td><td className="p-2 text-right">-0.50%</td><td className="p-2 text-right">0.00%</td><td className="p-2 text-right">0.30%</td><td className="p-2 text-right">0.00%</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Current Forward P/E</td><td className="p-2 text-right">21.3x</td><td className="p-2 text-right">14.9x</td><td className="p-2 text-right">21.9x</td><td className="p-2 text-right">11.7x</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Target P/E</td><td className="p-2 text-right">22.7x</td><td className="p-2 text-right">16.4x</td><td className="p-2 text-right">22.1x</td><td className="p-2 text-right">15.0x</td></tr>
                    </tbody>
                  </table>
                </div>

                <Card className="bg-amber-50 border-amber-200 mt-4">
                  <CardContent className="pt-4">
                    <p className="text-sm text-amber-700">
                      <strong>Key Differences vs RA Model:</strong> The GK model uses P/E ratios (not CAEY/CAPE) for valuation,
                      separates revenue growth from margin change (vs a single EPS growth component),
                      and explicitly includes net buyback yield. It also produces nominal returns directly,
                      making it easier to compare with observable market yields.
                    </p>
                  </CardContent>
                </Card>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Model Comparison */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-lg">Model Comparison: RA vs Grinold-Kroner</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-slate-800 text-white">
                    <th className="p-2 text-left">Feature</th>
                    <th className="p-2 text-left">RA Model</th>
                    <th className="p-2 text-left">Grinold-Kroner Model</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b"><td className="p-2 font-medium">Output</td><td className="p-2">Real return (add inflation for nominal)</td><td className="p-2">Nominal return directly</td></tr>
                  <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Valuation Metric</td><td className="p-2">CAEY (1/CAPE) — 20-year reversion</td><td className="p-2">Forward P/E — 10-year reversion</td></tr>
                  <tr className="border-b"><td className="p-2 font-medium">Growth Component</td><td className="p-2">Real EPS Growth (blended, GDP-capped)</td><td className="p-2">Revenue Growth + Margin Change (macro-linked)</td></tr>
                  <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Buyback Component</td><td className="p-2">Not explicit (in EPS growth)</td><td className="p-2">Explicit Net Buyback Yield</td></tr>
                  <tr className="border-b"><td className="p-2 font-medium">Macro Linkage</td><td className="p-2">Inflation (for nominal), GDP cap on EPS</td><td className="p-2">Inflation + GDP flow through Revenue Growth</td></tr>
                  <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Best For</td><td className="p-2">Long-term strategic allocation</td><td className="p-2">Understanding growth/margin/repricing drivers</td></tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Absolute Return */}
      <section id="absolute-return" className="mb-12">
        <h2 className="text-2xl font-bold text-slate-800 border-b-2 border-slate-800 pb-2 mb-4 flex items-center gap-2">
          <Target className="h-6 w-6" />
          Absolute Return (Hedge Funds)
        </h2>

        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 font-mono text-sm mb-6">
          <strong>E[HF Return] = E[T-Bill] + Σ(βᵢ × Factor Premiumᵢ) + Trading Alpha</strong>
        </div>

        <p className="mb-4">The hedge fund model uses the <strong>Fama-French factor framework</strong> to decompose returns.</p>

        <div className="overflow-x-auto mb-6">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-slate-800 text-white">
                <th className="p-2 text-left">Factor</th>
                <th className="p-2 text-left">Symbol</th>
                <th className="p-2 text-left">Default β</th>
                <th className="p-2 text-left">Historical Premium</th>
                <th className="p-2 text-left">Description</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b"><td className="p-2 font-medium">Market</td><td className="p-2">MKT-RF</td><td className="p-2">0.30</td><td className="p-2">Equity Return - T-Bill</td><td className="p-2">Equity market exposure</td></tr>
              <tr className="border-b"><td className="p-2 font-medium">Size</td><td className="p-2">SMB</td><td className="p-2">0.10</td><td className="p-2">2.0%</td><td className="p-2">Small minus Big</td></tr>
              <tr className="border-b"><td className="p-2 font-medium">Value</td><td className="p-2">HML</td><td className="p-2">0.05</td><td className="p-2">3.0%</td><td className="p-2">High minus Low B/M</td></tr>
              <tr className="border-b"><td className="p-2 font-medium">Profitability</td><td className="p-2">RMW</td><td className="p-2">0.05</td><td className="p-2">2.5%</td><td className="p-2">Robust minus Weak</td></tr>
              <tr className="border-b"><td className="p-2 font-medium">Investment</td><td className="p-2">CMA</td><td className="p-2">0.05</td><td className="p-2">2.5%</td><td className="p-2">Conservative minus Aggressive</td></tr>
              <tr className="border-b"><td className="p-2 font-medium">Momentum</td><td className="p-2">UMD</td><td className="p-2">0.10</td><td className="p-2">6.0%</td><td className="p-2">Up minus Down</td></tr>
            </tbody>
          </table>
        </div>

        <Card className="bg-slate-50">
          <CardContent className="pt-4">
            <h4 className="font-semibold mb-2">Trading Alpha</h4>
            <p className="font-mono text-sm bg-white p-2 rounded mb-2">Expected Alpha = 50% × Historical Alpha = 1.0%</p>
            <p className="text-sm text-slate-600">
              Alpha represents manager skill beyond systematic factor exposures.
              The 50% haircut accounts for alpha decay, survivor bias, and capacity constraints.
            </p>
          </CardContent>
        </Card>
      </section>

      {/* Default Assumptions */}
      <section id="default-assumptions" className="mb-12">
        <h2 className="text-2xl font-bold text-slate-800 border-b-2 border-slate-800 pb-2 mb-4 flex items-center gap-2">
          <Table className="h-6 w-6" />
          Default Assumptions
        </h2>
        <p className="mb-6 text-slate-600">
          Complete list of all default input assumptions used across the tool. These values are based on current market data
          and long-term estimates as of January 2026. Users can override any of these inputs in the dashboard.
        </p>

        <Tabs defaultValue="macro-defaults" className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="macro-defaults">Macro</TabsTrigger>
            <TabsTrigger value="bonds-defaults">Bonds</TabsTrigger>
            <TabsTrigger value="equity-defaults">Equity</TabsTrigger>
            <TabsTrigger value="alt-defaults">Absolute Return</TabsTrigger>
            <TabsTrigger value="vol-defaults">Volatility</TabsTrigger>
          </TabsList>

          {/* Macro Defaults */}
          <TabsContent value="macro-defaults" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Macro Economic Assumptions</CardTitle>
              </CardHeader>
              <CardContent>
                <h4 className="font-semibold mb-3">Building Block Inputs</h4>
                <div className="overflow-x-auto mb-6">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="bg-slate-800 text-white">
                        <th className="p-2 text-left">Input</th>
                        <th className="p-2 text-right">US</th>
                        <th className="p-2 text-right">Eurozone</th>
                        <th className="p-2 text-right">Japan</th>
                        <th className="p-2 text-right">EM</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b"><td className="p-2 font-medium">Current Headline Inflation</td><td className="p-2 text-right">3.00%</td><td className="p-2 text-right">2.00%</td><td className="p-2 text-right">1.50%</td><td className="p-2 text-right">4.00%</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Long-Term Inflation Target</td><td className="p-2 text-right">3.00%</td><td className="p-2 text-right">2.00%</td><td className="p-2 text-right">1.50%</td><td className="p-2 text-right">4.00%</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Current T-Bill Rate</td><td className="p-2 text-right">3.53%</td><td className="p-2 text-right">1.80%</td><td className="p-2 text-right">1.62%</td><td className="p-2 text-right">4.00%</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Country Factor</td><td className="p-2 text-right">0.00%</td><td className="p-2 text-right">-0.20%</td><td className="p-2 text-right">-0.50%</td><td className="p-2 text-right">-3.40%</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Population Growth</td><td className="p-2 text-right">0.40%</td><td className="p-2 text-right">0.10%</td><td className="p-2 text-right">-0.20%</td><td className="p-2 text-right">1.00%</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Productivity Growth</td><td className="p-2 text-right">1.20%</td><td className="p-2 text-right">1.49%</td><td className="p-2 text-right">1.59%</td><td className="p-2 text-right">2.44%</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">MY Ratio (Middle/Young)</td><td className="p-2 text-right">2.10</td><td className="p-2 text-right">2.30</td><td className="p-2 text-right">2.30</td><td className="p-2 text-right">1.50</td></tr>
                    </tbody>
                  </table>
                </div>

                <h4 className="font-semibold mb-3">Computed 10-Year Forecasts (from building blocks)</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="bg-blue-800 text-white">
                        <th className="p-2 text-left">Forecast</th>
                        <th className="p-2 text-right">US</th>
                        <th className="p-2 text-right">Eurozone</th>
                        <th className="p-2 text-right">Japan</th>
                        <th className="p-2 text-right">EM</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b"><td className="p-2 font-medium">E[Inflation] (10yr avg)</td><td className="p-2 text-right">3.00%</td><td className="p-2 text-right">2.00%</td><td className="p-2 text-right">1.50%</td><td className="p-2 text-right">4.00%</td></tr>
                      <tr className="border-b bg-blue-50"><td className="p-2 font-medium">E[Real GDP Growth] (10yr avg)</td><td className="p-2 text-right">1.20%</td><td className="p-2 text-right">1.00%</td><td className="p-2 text-right">0.80%</td><td className="p-2 text-right">3.40%</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">E[T-Bill Rate] (10yr avg)</td><td className="p-2 text-right">4.00%</td><td className="p-2 text-right">2.50%</td><td className="p-2 text-right">1.75%</td><td className="p-2 text-right">4.00%</td></tr>
                    </tbody>
                  </table>
                </div>

                <Card className="bg-blue-50 border-blue-200 mt-4">
                  <CardContent className="pt-4">
                    <p className="text-sm text-blue-700">
                      <strong>Note:</strong> The computed forecasts are derived from the building block inputs using the macro models
                      (30/70 weighting for inflation and T-Bill, GDP from population + productivity + demographics).
                      Users can override these forecasts directly, which takes priority over the building block computation.
                    </p>
                  </CardContent>
                </Card>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Bond Defaults */}
          <TabsContent value="bonds-defaults" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Bond Default Assumptions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="bg-slate-800 text-white">
                        <th className="p-2 text-left">Input</th>
                        <th className="p-2 text-right">Bonds Global</th>
                        <th className="p-2 text-right">Bonds HY</th>
                        <th className="p-2 text-right">Bonds EM</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b"><td className="p-2 font-medium">Current Yield</td><td className="p-2 text-right">4.60%</td><td className="p-2 text-right">7.10%</td><td className="p-2 text-right">6.00%</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Duration (years)</td><td className="p-2 text-right">8.0</td><td className="p-2 text-right">3.0</td><td className="p-2 text-right">5.8</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Current Term Premium</td><td className="p-2 text-right">0.81%</td><td className="p-2 text-right">1.00%</td><td className="p-2 text-right">0.81%</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Fair Term Premium</td><td className="p-2 text-right">1.00%</td><td className="p-2 text-right">1.00%</td><td className="p-2 text-right">1.00%</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Credit Spread</td><td className="p-2 text-right">--</td><td className="p-2 text-right">2.60%</td><td className="p-2 text-right">--</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Fair Credit Spread</td><td className="p-2 text-right">--</td><td className="p-2 text-right">4.00%</td><td className="p-2 text-right">--</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Default Rate</td><td className="p-2 text-right">--</td><td className="p-2 text-right">3.40%</td><td className="p-2 text-right">3.40%</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Recovery Rate</td><td className="p-2 text-right">--</td><td className="p-2 text-right">40.0%</td><td className="p-2 text-right">55.0%</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Annual Credit Loss</td><td className="p-2 text-right">0.00%</td><td className="p-2 text-right">2.04%</td><td className="p-2 text-right">1.53%</td></tr>
                    </tbody>
                  </table>
                </div>

                <Card className="bg-amber-50 border-amber-200 mt-4">
                  <CardContent className="pt-4">
                    <p className="text-sm text-amber-700">
                      <strong>Credit Loss Formula:</strong> Annual Credit Loss = Default Rate x (1 - Recovery Rate).
                      Bonds Global (government bonds) are assumed default-free.
                      Bonds EM uses US macro assumptions since they are USD-denominated hard currency bonds.
                    </p>
                  </CardContent>
                </Card>

                <Card className="bg-blue-50 border-blue-200 mt-4">
                  <CardContent className="pt-4">
                    <p className="text-sm text-blue-700">
                      <strong>Bonds Inflation Linked:</strong> Defaults are regime-specific. In USD base mode, the model uses
                      US TIPS assumptions; in EUR base mode, it uses EUR inflation-linked sovereign assumptions.
                      Inputs include current real yield, duration, real term premium, inflation beta, index lag drag,
                      and liquidity/technical adjustment.
                    </p>
                  </CardContent>
                </Card>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Equity Defaults */}
          <TabsContent value="equity-defaults" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Equity Default Assumptions</CardTitle>
              </CardHeader>
              <CardContent>
                <h4 className="font-semibold mb-3">RA Model (CAEY-Based)</h4>
                <div className="overflow-x-auto mb-6">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="bg-slate-800 text-white">
                        <th className="p-2 text-left">Input</th>
                        <th className="p-2 text-right">US</th>
                        <th className="p-2 text-right">Europe</th>
                        <th className="p-2 text-right">Japan</th>
                        <th className="p-2 text-right">EM</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b"><td className="p-2 font-medium">Dividend Yield</td><td className="p-2 text-right">1.13%</td><td className="p-2 text-right">3.00%</td><td className="p-2 text-right">2.20%</td><td className="p-2 text-right">3.00%</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Current CAEY (1/CAPE)</td><td className="p-2 text-right">2.48%</td><td className="p-2 text-right">5.50%</td><td className="p-2 text-right">5.50%</td><td className="p-2 text-right">6.50%</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Fair CAEY</td><td className="p-2 text-right">5.00%</td><td className="p-2 text-right">5.50%</td><td className="p-2 text-right">5.00%</td><td className="p-2 text-right">6.00%</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Implied CAPE (Current)</td><td className="p-2 text-right">40.3x</td><td className="p-2 text-right">18.2x</td><td className="p-2 text-right">18.2x</td><td className="p-2 text-right">15.4x</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Implied CAPE (Fair)</td><td className="p-2 text-right">20.0x</td><td className="p-2 text-right">18.2x</td><td className="p-2 text-right">20.0x</td><td className="p-2 text-right">16.7x</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Country Real EPS Growth</td><td className="p-2 text-right">1.80%</td><td className="p-2 text-right">1.20%</td><td className="p-2 text-right">0.80%</td><td className="p-2 text-right">3.00%</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Regional EPS Growth</td><td className="p-2 text-right">1.60%</td><td className="p-2 text-right">1.60%</td><td className="p-2 text-right">1.60%</td><td className="p-2 text-right">2.80%</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Blended EPS Growth</td><td className="p-2 text-right">1.70%</td><td className="p-2 text-right">1.40%</td><td className="p-2 text-right">1.20%</td><td className="p-2 text-right">2.90%</td></tr>
                    </tbody>
                  </table>
                </div>

                <h4 className="font-semibold mb-3">Grinold-Kroner Model (P/E-Based)</h4>
                <div className="overflow-x-auto mb-4">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="bg-purple-800 text-white">
                        <th className="p-2 text-left">Input</th>
                        <th className="p-2 text-right">US</th>
                        <th className="p-2 text-right">Europe</th>
                        <th className="p-2 text-right">Japan</th>
                        <th className="p-2 text-right">EM</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b"><td className="p-2 font-medium">Dividend Yield</td><td className="p-2 text-right">1.10%</td><td className="p-2 text-right">2.80%</td><td className="p-2 text-right">1.90%</td><td className="p-2 text-right">2.20%</td></tr>
                      <tr className="border-b bg-purple-50"><td className="p-2 font-medium">Net Buyback Yield</td><td className="p-2 text-right">1.30%</td><td className="p-2 text-right">0.70%</td><td className="p-2 text-right">1.40%</td><td className="p-2 text-right">-0.60%</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Revenue-GDP Wedge</td><td className="p-2 text-right">2.00%</td><td className="p-2 text-right">0.50%</td><td className="p-2 text-right">0.50%</td><td className="p-2 text-right">0.50%</td></tr>
                      <tr className="border-b bg-purple-50"><td className="p-2 font-medium">Margin Change</td><td className="p-2 text-right">-0.50%</td><td className="p-2 text-right">0.00%</td><td className="p-2 text-right">+0.30%</td><td className="p-2 text-right">0.00%</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Current Forward P/E</td><td className="p-2 text-right">21.3x</td><td className="p-2 text-right">14.9x</td><td className="p-2 text-right">21.9x</td><td className="p-2 text-right">11.7x</td></tr>
                      <tr className="border-b bg-purple-50"><td className="p-2 font-medium">Target P/E</td><td className="p-2 text-right">22.7x</td><td className="p-2 text-right">16.4x</td><td className="p-2 text-right">22.1x</td><td className="p-2 text-right">15.0x</td></tr>
                    </tbody>
                  </table>
                </div>

                <Card className="bg-purple-50 border-purple-200 mt-4">
                  <CardContent className="pt-4">
                    <p className="text-sm text-purple-700">
                      <strong>Revenue Growth</strong> is not listed above because it is auto-computed from macro:
                      Revenue Growth = Regional Inflation + Regional GDP + Wedge. For example, US default ≈ 3.00% + 1.20% + 2.00% = 6.20%.
                      The Revenue-GDP Wedge captures how corporate revenue growth differs from nominal GDP (e.g., US companies have global revenue exposure).
                    </p>
                  </CardContent>
                </Card>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Absolute Return Defaults */}
          <TabsContent value="alt-defaults" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Absolute Return (Hedge Fund) Default Assumptions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="bg-slate-800 text-white">
                        <th className="p-2 text-left">Factor</th>
                        <th className="p-2 text-right">Beta Exposure</th>
                        <th className="p-2 text-right">Historical Premium</th>
                        <th className="p-2 text-right">Contribution</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b"><td className="p-2 font-medium">Market (MKT-RF)</td><td className="p-2 text-right">0.30</td><td className="p-2 text-right">E[Equity] - E[T-Bill]</td><td className="p-2 text-right">Dynamic</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Size (SMB)</td><td className="p-2 text-right">0.10</td><td className="p-2 text-right">2.00%</td><td className="p-2 text-right">0.20%</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Value (HML)</td><td className="p-2 text-right">0.05</td><td className="p-2 text-right">3.00%</td><td className="p-2 text-right">0.15%</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Profitability (RMW)</td><td className="p-2 text-right">0.05</td><td className="p-2 text-right">2.50%</td><td className="p-2 text-right">0.13%</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Investment (CMA)</td><td className="p-2 text-right">0.05</td><td className="p-2 text-right">2.50%</td><td className="p-2 text-right">0.13%</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Momentum (UMD)</td><td className="p-2 text-right">0.10</td><td className="p-2 text-right">6.00%</td><td className="p-2 text-right">0.60%</td></tr>
                      <tr className="border-b font-semibold"><td className="p-2">Trading Alpha</td><td className="p-2 text-right">--</td><td className="p-2 text-right">~2.00% (historical)</td><td className="p-2 text-right">1.00%</td></tr>
                    </tbody>
                  </table>
                </div>

                <Card className="bg-slate-50 border-slate-200 mt-4">
                  <CardContent className="pt-4">
                    <p className="text-sm text-slate-700">
                      <strong>Total Return Formula:</strong> E[HF Return] = E[T-Bill] + Market Beta Contribution + Factor Premia + Trading Alpha.
                      Factor premia use 50% of historical estimates. Trading alpha of 1.00% = 50% haircut on ~2% historical alpha
                      to account for alpha decay, survivorship bias, and capacity constraints.
                    </p>
                  </CardContent>
                </Card>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Volatility Defaults */}
          <TabsContent value="vol-defaults" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Expected Volatility (Long-Term Historical Estimates)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="bg-slate-800 text-white">
                        <th className="p-2 text-left">Asset Class</th>
                        <th className="p-2 text-right">Expected Volatility</th>
                        <th className="p-2 text-left">Notes</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b"><td className="p-2 font-medium">Liquidity</td><td className="p-2 text-right">1.0%</td><td className="p-2 text-slate-600">Cash / T-Bills, minimal volatility</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Bonds Global</td><td className="p-2 text-right">6.0%</td><td className="p-2 text-slate-600">DM government bonds, duration-driven</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Bonds HY</td><td className="p-2 text-right">10.0%</td><td className="p-2 text-slate-600">Credit spread volatility adds to rate vol</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Bonds EM</td><td className="p-2 text-right">12.0%</td><td className="p-2 text-slate-600">EM sovereign credit + rate volatility</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Equity US</td><td className="p-2 text-right">16.0%</td><td className="p-2 text-slate-600">S&P 500 long-term historical</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Equity Europe</td><td className="p-2 text-right">18.0%</td><td className="p-2 text-slate-600">MSCI Europe, slightly higher than US</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Equity Japan</td><td className="p-2 text-right">18.0%</td><td className="p-2 text-slate-600">MSCI Japan, currency adds vol for foreign investors</td></tr>
                      <tr className="border-b bg-slate-50"><td className="p-2 font-medium">Equity EM</td><td className="p-2 text-right">24.0%</td><td className="p-2 text-slate-600">MSCI EM, includes FX and political risk</td></tr>
                      <tr className="border-b"><td className="p-2 font-medium">Absolute Return</td><td className="p-2 text-right">8.0%</td><td className="p-2 text-slate-600">Diversified hedge fund composite</td></tr>
                    </tbody>
                  </table>
                </div>

                <Card className="bg-blue-50 border-blue-200 mt-4">
                  <CardContent className="pt-4">
                    <p className="text-sm text-blue-700">
                      <strong>Note:</strong> These volatility estimates are used for the Risk-Return Profile chart.
                      They represent long-term annualised standard deviations and are not currently user-adjustable.
                      Volatility figures are based on historical data and may not reflect future conditions.
                    </p>
                  </CardContent>
                </Card>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </section>

      {/* FAQ */}
      <section id="faq" className="mb-12">
        <h2 className="text-2xl font-bold text-slate-800 border-b-2 border-slate-800 pb-2 mb-4">
          Frequently Asked Questions
        </h2>

        <Accordion type="single" collapsible className="w-full">
          <AccordionItem value="item-1">
            <AccordionTrigger>Why are US equity returns lower than historical averages?</AccordionTrigger>
            <AccordionContent>
              <p className="mb-2">US equity returns in the model may be lower than historical averages (10%+) for several reasons:</p>
              <ol className="list-decimal list-inside space-y-2">
                <li><strong>High Valuations</strong>: Current CAEY of 2.48% (CAPE ~40) is below fair value of 5.0% (CAPE ~20). This creates a valuation headwind.</li>
                <li><strong>Lower Dividend Yields</strong>: Current yields (~1.13%) are near all-time lows vs historical averages (~4%).</li>
                <li><strong>Building Block Approach</strong>: The model builds returns from fundamentals rather than extrapolating historical returns.</li>
              </ol>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="item-2">
            <AccordionTrigger>Why is there a GDP cap on EPS growth?</AccordionTrigger>
            <AccordionContent>
              <p>Corporate earnings cannot grow faster than the economy indefinitely because profits are a share of GDP. If profits grew faster than GDP, they would eventually exceed 100% of GDP (impossible). The cap prevents overly optimistic assumptions in high-growth regions.</p>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="item-3">
            <AccordionTrigger>What's the difference between Basic and Advanced mode?</AccordionTrigger>
            <AccordionContent>
              <p className="mb-2"><strong>Basic Mode</strong> provides direct forecast overrides (E[Inflation], E[GDP], E[T-Bill]) and primary asset inputs.</p>
              <p><strong>Advanced Mode</strong> adds building block inputs (population growth, productivity, MY ratio) and full control over how forecasts are computed.</p>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="item-4">
            <AccordionTrigger>How should I interpret negative valuation returns?</AccordionTrigger>
            <AccordionContent>
              <p className="mb-2">Negative valuation returns indicate that current valuations are <strong>expensive</strong> relative to fair value:</p>
              <ul className="list-disc list-inside space-y-1">
                <li><strong>Bonds</strong>: Negative valuation = term premiums expected to rise → yields rise → prices fall</li>
                <li><strong>Equities</strong>: Negative valuation = CAEY expected to rise → CAPE expected to fall → P/E compression</li>
              </ul>
              <p className="mt-2">Total return can still be positive if yield and growth components are large enough.</p>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="item-5">
            <AccordionTrigger>How do I use the asset breakdown feature?</AccordionTrigger>
            <AccordionContent>
              <p className="mb-2">Click on any asset class row in the results table to expand a detailed breakdown showing:</p>
              <ul className="list-disc list-inside space-y-1">
                <li>The main return formula for that asset class</li>
                <li>A waterfall chart showing return attribution by component</li>
                <li>Component details with formulas and current input values</li>
                <li>Blue badges with * indicate values you've overridden from defaults</li>
              </ul>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="item-6">
            <AccordionTrigger>What is the difference between the RA and Grinold-Kroner equity models?</AccordionTrigger>
            <AccordionContent>
              <p className="mb-2">The <strong>RA Model</strong> uses CAEY (cyclically adjusted earnings yield) for valuation and produces a <strong>real</strong> return (DY + EPS Growth + Valuation). You add inflation to get nominal.</p>
              <p className="mb-2">The <strong>Grinold-Kroner Model</strong> uses forward P/E for valuation and produces a <strong>nominal</strong> return directly (DY + Buyback + Revenue Growth + Margin Change + Valuation). Revenue growth is auto-computed from macro unless overridden.</p>
              <p>Use the toggle in the <strong>Equity</strong> input tab to switch between them. All four equity regions switch together.</p>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="item-7">
            <AccordionTrigger>Why does Revenue Growth differ from what I entered?</AccordionTrigger>
            <AccordionContent>
              <p className="mb-2">In the GK model, Revenue Growth is <strong>auto-computed</strong> from macro forecasts:</p>
              <p className="font-mono text-sm bg-slate-100 p-2 rounded mb-2">Revenue Growth = Regional Inflation + Regional Real GDP + Revenue-GDP Wedge</p>
              <p className="mb-2">The input field shows a static default (e.g., 2.5% for Japan) but the actual calculation uses the live macro-derived value. If you want to use a specific value, type it directly into the field — this marks it as a user override and breaks the macro link.</p>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="item-8">
            <AccordionTrigger>What happens when I switch to EUR base currency?</AccordionTrigger>
            <AccordionContent>
              <p className="mb-2">Three things change:</p>
              <ol className="list-decimal list-inside space-y-2">
                <li><strong>Liquidity & Absolute Return</strong> switch to the Eurozone T-Bill rate (instead of US T-Bill).</li>
                <li><strong>Non-EUR assets</strong> (US bonds, US/Japan/EM equities) get an FX adjustment added, based on carry (T-Bill differential) and PPP (inflation differential).</li>
                <li>A <strong>Currency Adjustment card</strong> appears on the dashboard showing the FX methodology, per-pair breakdown, and per-asset impact.</li>
              </ol>
              <p className="mt-2">EUR-denominated assets (Equity Europe) are unaffected. All bond classes remain priced off US rates since they are USD-denominated instruments.</p>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="item-9">
            <AccordionTrigger>How often should default values be updated?</AccordionTrigger>
            <AccordionContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr className="bg-slate-100">
                      <th className="p-2 text-left">Input Type</th>
                      <th className="p-2 text-left">Update Frequency</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b"><td className="p-2">Current yields, T-Bills</td><td className="p-2">Monthly or more</td></tr>
                    <tr className="border-b"><td className="p-2">Dividend yields, CAEY</td><td className="p-2">Quarterly</td></tr>
                    <tr className="border-b"><td className="p-2">Macro forecasts (GDP, inflation)</td><td className="p-2">Quarterly</td></tr>
                    <tr className="border-b"><td className="p-2">Fair values (EWMA-based)</td><td className="p-2">Annually</td></tr>
                  </tbody>
                </table>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </section>

      {/* Footer */}
      <div className="border-t pt-6 text-center text-sm text-slate-500">
        <p><strong>Parkview CMA Methodology Reference</strong></p>
        <p className="mt-1">
          <Link href="/" className="text-blue-600 hover:underline">Return to Dashboard</Link> to run stress tests.
        </p>
      </div>
    </div>
  );
}
