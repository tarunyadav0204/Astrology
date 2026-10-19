import { buildBhriguBinduReport } from './bhriguBinduExport';
test('report escapes notes and exports Bindu facts without MB labels', () => {
 const html=buildBhriguBinduReport({natal:{source:'Patel',degree_semantics:'Forward Rahu-to-Moon',points:[{point:'Bhrigu Bindu',position:'Taurus 29°',house:2,nakshatra:'Mrigashira',pada:2,nakshatra_lord:'Mars',moon_position:'Libra',rahu_position:'Capricorn',forward_arc_degrees:265,dispositor:'Venus',relationships:[]}]},range:{},audit:{sources:[],limits:[]},birth_time_comparison:[],dasha_activations:[],calendar_calculated:false,schema_version:'v1'}, {name:'<script>alert(1)</script>'}, {'Bhrigu Bindu':'<b>note</b>'}, []);
 expect(html).toContain('Bhrigu Bindu');
 expect(html).toContain('Forward Rahu-to-Moon');
 expect(html).toContain('&lt;b&gt;note&lt;/b&gt;');
 expect(html).not.toContain('<script>');
 expect(html).not.toContain('Mrityu Bhaga');
 expect(html).toContain('Calendar has not been calculated');
});
