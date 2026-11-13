const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const test = require('node:test');
const parser = require('@babel/parser');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../src/credits/CreditScreen.js'), 'utf8');
parser.parse(source, {sourceType:'module',plugins:['jsx']});
const begin=source.indexOf('  const handleGooglePlayPurchaseSuccess =');
const end=source.indexOf('  const closePurchaseModal',begin);
const listenerBegin=source.indexOf('RNIap.purchaseUpdatedListener(async (purchase) => {');
const listenerEnd=source.indexOf('\n        errorSub =',listenerBegin);
function setup(response, fail=false) {
  const events=[];
  const noop=()=>{};
  const sandbox={
    creditCheckoutInFlightRef:{current:true}, setPurchasingProductId:noop, iapProducts:[],
    packAcceptsPurchasePromo:()=>false, checkoutPromo:null,
    savePendingGooglePlayCreditPurchase:async()=>events.push('saved'),
    removePendingGooglePlayCreditPurchase:async()=>events.push('removed'),
    creditAPI:{verifyGooglePlayPurchase:async()=>{if(fail)throw new Error('network');return {data:response}},reportPaymentFailure:async()=>{}},
    fetchBalance:async()=>{},fetchHistory:async()=>{},fetchProducts:async()=>{},setGooglePlayProducts:noop,
    setPurchaseModal:noop,t:(s)=>s,googlePlayProducts:[],getIapPriceNumber:()=>0,getIapCurrency:()=>null,
    trackAstrologyEvent:{creditPurchased:noop,addPaymentInfo:noop},
    subscriptionProductIds:[],subscriptionPlans:[],productIds:['credits_24'],
    creditsFromGooglePlayProductId:()=>24,console:{warn:noop},
    RNIap:{purchaseUpdatedListener:(cb)=>{sandbox.listener=cb},finishTransaction:async()=>events.push('finished')},
  };
  vm.createContext(sandbox);
  vm.runInContext(source.slice(begin,end),sandbox);
  vm.runInContext(source.slice(listenerBegin,listenerEnd),sandbox);
  return {events,run:()=>sandbox.listener({purchaseToken:'token',productId:'credits_24',transactionId:'GPA.test'})};
}
for(const [name,response,fail,finished] of [
 ['network failure',null,true,false],['unconfirmed response',{success:false},false,false],
 ['paid purchase',{success:true,credits_added:24},false,true],
 ['replayed purchase',{success:true,credits_added:0,message:'Already credited'},false,true],
 ['canceled purchase',{success:false,terminal:true,purchase_state:1},false,true],
]) test(name,async()=>{
 const {events,run}=setup(response,fail);await run();
 assert.equal(events.includes('finished'),finished);
 assert.equal(events.includes('removed'),finished);
});
