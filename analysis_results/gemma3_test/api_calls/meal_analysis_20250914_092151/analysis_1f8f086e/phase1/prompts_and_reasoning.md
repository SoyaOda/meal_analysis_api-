# Phase1: 画像分析 - プロンプトと推論

## 実行情報
- 実行ID: 1f8f086e_phase1
- 開始時刻: 2025-09-14T09:21:51.496540
- 終了時刻: 2025-09-14T09:22:07.278328
- 実行時間: 15.78秒

## 使用されたプロンプト

### Structured System Prompt

**タイムスタンプ**: 2025-09-14T09:21:51.499139

```
You are an advanced food recognition AI that analyzes food images and provides detailed structured output for nutrition calculation.


MYNETDIARY INGREDIENT CONSTRAINT:
For ALL ingredients, you MUST select ONLY from the following MyNetDiary ingredient list. 
Do NOT create custom ingredient names. Use the EXACT names as they appear in this list:

1. Agave syrup
2. Allspice ground
3. Almond butter with salt
4. Almond butter without salt
5. Almond extract
6. Almond flour
7. Almond meal
8. Almond milk unsweetened fortified
9. Almond oil
10. Almond yogurt plain
11. Almonds dry roasted with salt
12. Almonds dry roasted without salt
13. Almonds oil roasted with salt
14. Almonds raw
15. Ancho chile powder
16. Anchovy canned
17. Anchovy raw
18. Angelica wine
19. Apple juice canned or bottled unsweetened fortified with Vitamin C
20. Apple juice canned or bottled unsweetened not fortified
21. Apples dried
22. Apples with skin raw
23. Apples without skin or peeled raw
24. Apricots dried
25. Apricots raw
26. Arrowroot flour
27. Artichokes boiled without salt
28. Artichokes raw
29. Arugula or rocket raw
30. Asparagus boiled with salt
31. Asparagus boiled without salt
32. Asparagus raw
33. Asparagus steamed
34. Avocado oil
35. Avocados raw
36. Baby spinach
37. Bagel plain onion poppy or sesame
38. Baker's yeast active dry
39. Baker's yeast compressed
40. Baking powder
41. Baking soda
42. Balls of honeydew melon, frozen
43. Balsamic Vinaigrette Dressing
44. Balsamic Vinegar
45. Bananas raw
46. Barbecue Sauce or BBQ
47. Barley flour or meal
48. Barley hulled raw
49. Barley pearled dry uncooked
50. Basil dried
51. Basil fresh or raw herb
52. Bay leaf
53. Beans baked canned plain or vegetarian
54. Beaujolais wine
55. Beef brisket flat cut trimmed to 1/8" fat raw
56. Beef broth dry cubes
57. Beef broth or bouillon canned
58. Beef broth or bouillon dry powder
59. Beef broth or bouillon prepared from dry powder
60. Beef broth prepared from dry cubes
61. Beef broth reduced sodium canned
62. Beef chuck arm pot roast lean and fat trimmed to 1/8" fat raw
63. Beef chuck short ribs boneless lean and fat trimmed to 0" fat raw
64. Beef flank steak lean and fat trimmed to 0" raw
65. Beef ground 70% lean 30% fat raw
66. Beef ground 75% lean 25% fat raw
67. Beef ground 80% lean 20% fat or hamburger patty raw
68. Beef ground 85% lean 15% fat raw
69. Beef ground 90% lean 10% fat raw
70. Beef ground 93% lean 7% fat raw
71. Beef ground 95% lean 5% fat raw
72. Beef ground 97% lean 3% fat raw
73. Beef ground grass fed raw
74. Beef jerky sweet and hot
75. Beef liver cooked pan-fried
76. Beef liver raw
77. Beef ribeye steak bone-in lean and trimmed to 1/8" fat all grades raw
78. Beef ribeye steak boneless lean and trimmed to 1/8" fat all grades raw
79. Beef round tip lean and fat trimmed to 1/8" raw
80. Beef round top steak boneless lean and trimmed to 0" fat all grades raw
81. Beef short or top loin lean and trimmed to 1/8" fat all grades raw
82. Beef stock homemade
83. Beef tenderloin boneless lean meat only cooked roasted
84. Beef tongue raw
85. Beef top sirloin steak lean and fat trimmed to 1/8" raw
86. Beer 7.7% ABV
87. Beer Guinness stout 4.2% ABV
88. Beer regular 5% ABV
89. Beet greens raw
90. Beets canned drained
91. Beets raw
92. Berries mixed frozen unsweetened
93. Bison ground raw
94. Black bean spaghetti pasta dry uncooked
95. Black beans boiled without salt
96. Black beans canned
97. Black beans canned low sodium
98. Black beans canned no salt added
99. Black beans raw
100. Black eyed peas boiled without salt
101. Black eyed peas canned
102. Black eyed peas raw
103. Black russian cocktail
104. Blackberries frozen unsweetened
105. Blackberries raw
106. Blue cheese
107. Blueberries frozen unsweetened
108. Blueberries raw
109. Bok choy or pak choi or Chinese cabbage raw
110. Bordeaux red wine
111. Brandy Alexander
112. Brazil nuts or brazilnuts
113. Bread crumbs dry grated plain
114. Bread crumbs dry grated seasoned
115. Bread crumbs panko
116. Bread crumbs whole wheat dry grated
117. Brick cheese
118. Brie cheese
119. Broccoli Chinese raw
120. Broccoli boiled without salt
121. Broccoli florets raw
122. Broccoli frozen unprepared
123. Broccoli raab rabe or rapini raw
124. Broccoli raw
125. Broccoli roasted without salt
126. Broccoli steamed
127. Broccolini raw
128. Brown sugar
129. Brown sugar baking blend (sucralose and brown sugar)
130. Brown sugar baking blend with erythritol and stevia
131. Brussels sprouts boiled without salt
132. Brussels sprouts frozen unprepared
133. Brussels sprouts raw
134. Buckwheat groats or kasha cooked without salt
135. Buckwheat groats or kasha roasted dry uncooked
136. Buffalo wing sauce bottled
137. Bulgur cooked
138. Bulgur dry uncooked
139. Butter reduced fat salted
140. Butter reduced fat unsalted
141. Butter salted
142. Butter unsalted
143. Butter whipped salted
144. Butter whipped unsalted
145. Buttermilk 1% low fat
146. Buttermilk 2% reduced fat
147. Buttermilk nonfat
148. Buttermilk regular whole
149. Cabbage raw
150. Cabbage red raw
151. Cabbage savoy raw
152. Cajun seasoning salt free
153. Cake flour white
154. Camembert cheese
155. Cannellini or white kidney beans canned
156. Cannellini or white kidney beans canned no salt added
157. Canola oil
158. Cantaloupe melon raw
159. Capers canned
160. Carbonated club soda
161. Carbonated cola regular
162. Carbonated ginger ale
163. Carbonated tonic water
164. Cardamom
165. Carrots baby raw
166. Carrots raw
167. Casaba melon raw
168. Cashew butter with salt
169. Cashew butter without salt
170. Cashew milk unsweetened
171. Cashew yogurt plain unsweetened
172. Cashews dry roasted with salt
173. Cashews dry roasted without salt
174. Cashews oil roasted with salt
175. Cashews oil roasted without salt
176. Cashews raw
177. Cassava or manioc raw
178. Catfish farmed cooked dry heat
179. Catfish farmed raw
180. Catfish wild raw
181. Cauliflower boiled without salt
182. Cauliflower frozen unprepared
183. Cauliflower raw
184. Cauliflower riced frozen unprepared
185. Cauliflower steamed
186. Celery raw
187. Celery root or celeriac raw
188. Chablis wine
189. Challah or egg bread
190. Champagne
191. Chapati or roti bread
192. Chapati or roti whole wheat bread
193. Chayote fruit or mirliton squash raw
194. Cheddar cheese
195. Cheddar or colby cheese low fat
196. Cherries maraschino canned
197. Cherries sour red frozen unsweetened
198. Cherries sour red raw
199. Cherries sweet frozen sweetened
200. Cherries sweet raw
201. Cherries tart sweetened dried
202. Cheshire cheese
203. Chestnuts roasted peeled
204. Chia seeds
205. Chicken breast baked boneless skinless
206. Chicken breast boneless skinless raw
207. Chicken breast grilled boneless skinless
208. Chicken breast tenderloins
209. Chicken broth canned
210. Chicken broth dry cubes
211. Chicken broth low sodium canned
212. Chicken broth or bouillon dry powder
213. Chicken broth or bouillon prepared from dry powder
214. Chicken broth prepared from dry cubes
215. Chicken broth reduced sodium canned
216. Chicken drumstick skinless raw
217. Chicken fat
218. Chicken giblets raw
219. Chicken ground raw
220. Chicken liver all classes cooked simmered
221. Chicken liver raw
222. Chicken or turkey sausage Italian low sodium
223. Chicken stock homemade
224. Chicken thigh meat and skin raw
225. Chicken thigh meat only raw
226. Chicken whole meat and skin raw
227. Chicken wing meat and skin raw
228. Chickpea or garbanzo bean flour
229. Chickpea pasta dry uncooked
230. Chickpea pasta wheels dry uncooked
231. Chickpeas or garbanzo beans boiled with salt
232. Chickpeas or garbanzo beans boiled without salt
233. Chickpeas or garbanzo beans canned
234. Chickpeas or garbanzo beans canned no salt added
235. Chickpeas or garbanzo beans raw
236. Chicory greens raw
237. Chili chipotle powder
238. Chili flakes or crushed red pepper spice
239. Chili garlic sauce or tuong ot toi Vietnam
240. Chili powder
241. Chives fresh or raw herb
242. Chocolate chips semi-sweet
243. Chocolate chips vegan
244. Chocolate for baking unsweetened
245. Chocolate fudge with chocolate cover
246. Chocolate milk 1% low fat
247. Chocolate milk 2% reduced fat
248. Chocolate milk regular whole
249. Chocolate syrup
250. Cilantro or coriander leaves dried
251. Cilantro or coriander leaves fresh or raw herb
252. Cinnamon ground
253. Cinnamon stick spice
254. Cinnamon sugar blend
255. Clams cooked moist heat
256. Clams raw
257. Clementines raw
258. Cloves ground
259. Club soda no sodium
260. Cocktail sauce
261. Cocoa butter
262. Cocoa powder dry unsweetened
263. Coconut aminos
264. Coconut cream raw
265. Coconut flour
266. Coconut meat dried unsweetened
267. Coconut meat raw
268. Coconut milk beverage unsweetened
269. Coconut milk canned light
270. Coconut milk canned regular
271. Coconut milk raw
272. Coconut oil
273. Coconut shredded unsweetened packaged
274. Coconut sugar
275. Coconut water raw
276. Coconut yogurt plain unsweetened fortified
277. Cod Atlantic dried and salted
278. Cod Atlantic raw
279. Cod Pacific cooked dry heat
280. Cod Pacific raw
281. Cod liver fish oil
282. Coffee black no sugar
283. Coffee decaf prepared without milk or sugar
284. Coffee regular instant powder
285. Cognac
286. Colby cheese
287. Collard greens boiled without salt
288. Collard greens raw
289. Cones sugar or rolled type for ice cream
290. Cones wafer or cake type for ice cream
291. Cooking wine
292. Coriander seed ground or whole dried
293. Corn flour masa white
294. Corn flour masa yellow
295. Corn flour whole-grain white
296. Corn flour whole-grain yellow
297. Corn oil
298. Corn sweet white canned
299. Corn sweet white raw
300. Corn sweet yellow boiled without salt
301. Corn sweet yellow canned
302. Corn sweet yellow canned cream style
303. Corn sweet yellow canned cream style no salt added
304. Corn sweet yellow canned no salt added
305. Corn sweet yellow frozen kernels unprepared
306. Corn sweet yellow raw
307. Corn syrup dark
308. Corn syrup light
309. Cornmeal whole-grain white
310. Cornmeal whole-grain yellow
311. Cornstarch
312. Cottage cheese low fat 1% milkfat
313. Cottage cheese reduced fat 2% milkfat
314. Cottage cheese whole 4% milkfat
315. Couscous or cous cous cooked without salt
316. Couscous or cous cous dry uncooked
317. Crab Alaska king raw
318. Crab Dungeness raw
319. Crab blue canned
320. Crab blue cooked moist heat
321. Crab blue raw
322. Crab queen or snow raw
323. Crackers gluten free multiseed and multigrain
324. Crackers whole wheat
325. Cranberries raw
326. Cranberries sweetened dried
327. Cream cheese
328. Cream cheese fat free
329. Cream cheese low fat
330. Cream half & half
331. Cream half & half fat-free
332. Cream half and half low fat
333. Cream heavy whipping
334. Cream light whipping
335. Cream sour
336. Cream sour fat free
337. Cream sour light
338. Cream whipped topping from can
339. Crispbread multigrain
340. Croutons seasoned
341. Cucumber peeled raw
342. Cucumber with peel raw
343. Cumin seed ground or whole
344. Currants european black raw
345. Currants red and white raw
346. Currants zante dried
347. Curry paste red
348. Curry powder
349. Dandelion greens raw
350. Dark chocolate 45 - 59% cacao
351. Dark chocolate 60 - 69% cacao
352. Dark chocolate 70 - 85% cacao
353. Dates deglet noor
354. Dates medjool
355. Deer ground raw
356. Deer meat raw
357. Diet tonic water
358. Dill seed ground or whole
359. Dill weed dried
360. Dill weed fresh or raw herb
361. Duck meat only raw
362. Duck wild meat and skin raw
363. Durian fruit raw or frozen
364. Edam cheese
365. Edamame dry roasted
366. Edamame frozen prepared or cooked
367. Edamame frozen unprepared
368. Edamame shelled or mukimame frozen unprepared
369. Eel cooked dry heat
370. Eel raw
371. Egg replacer
372. Egg scrambled, with salt
373. Egg substitute liquid or frozen fat free
374. Egg white raw
375. Egg whole fried
376. Egg whole hard boiled
377. Egg whole omelet
378. Egg whole poached
379. Egg whole raw
380. Egg yolk raw
381. Eggplant boiled without salt
382. Eggplant raw
383. Elbow macaroni dry uncooked
384. Elk ground raw
385. Endive raw
386. English muffin
387. English muffin whole wheat
388. Erythritol sweetener granular
389. Erythritol sweetener powdered or confectioners
390. Espresso decaf prepared without milk or sugar
391. Espresso regular prepared without milk or sugar
392. Everything bagel seasoning by stonemill
393. Everything bagel seasoning salt free
394. Fajita seasoning mix
395. Farro cooked
396. Fava beans boiled without salt
397. Fava beans raw
398. Feijoa raw
399. Fennel bulb raw
400. Fennel seed ground or whole
401. Feta cheese
402. Figs dried
403. Figs raw
404. Fingerling potatoes
405. Fish broth
406. Fish roe mixed species cooked dry heat
407. Fish roe mixed species raw
408. Fish sauce
409. Flax milk unsweetened fortified
410. Flaxseed or flax oil
411. Flaxseeds
412. Flour gluten free all purpose
413. Flour white all purpose
414. Flour white for bread making
415. Flour whole wheat
416. Flour whole wheat pastry
417. Fontina cheese
418. French vienna or sourdough bread
419. Fructose dry powder
420. Fructose liquid sweetener
421. Fruit cocktail canned in juice not drained
422. Garden cress raw
423. Garlic powder
424. Garlic raw
425. Gimlet cocktail
426. Gin rum vodka or whiskey 80 proof
427. Ginger ground dry
428. Ginger root raw
429. Goat cheese hard
430. Goat cheese soft
431. Goat's milk
432. Gooseberries raw
433. Gouda cheese
434. Grape juice unsweetened
435. Grape leaves raw
436. Grapefruit juice pink raw
437. Grapefruit juice white raw
438. Grapefruit pink or red raw
439. Grapefruit white raw
440. Grapes American raw
441. Grapes red or green raw
442. Grapeseed oil
443. Grasshopper cocktail
444. Gravy au jus canned
445. Greek yogurt plain low fat
446. Greek yogurt plain nonfat
447. Greek yogurt plain whole milk
448. Greek yogurt vanilla nonfat
449. Green beans boiled without salt
450. Green beans canned drained
451. Green beans frozen unprepared
452. Green beans raw
453. Green peas frozen boiled without salt
454. Green peas frozen unprepared
455. Green peas raw
456. Grouper mixed species raw
457. Gruyere cheese
458. Guacamole
459. Guavas common raw
460. Guavas strawberry raw
461. Haddock raw
462. Haddock smoked
463. Halibut raw
464. Ham boneless spiral sliced lean meat only roasted
465. Hamburger or hot dog buns white
466. Hamburger or hot dog buns whole wheat
467. Hard seltzer lemonade 5% ABV
468. Hazelnuts or filberts
469. Hazelnuts or filberts dry roasted without salt
470. Hemp milk unsweetened fortified
471. Hemp seeds shelled or hulled
472. Herring Atlantic cooked dry heat
473. Herring Atlantic kippered
474. Herring Atlantic pickled
475. Herring Atlantic raw
476. Hoisin Sauce
477. Hominy canned white
478. Honey
479. Honeydew melon raw
480. Horseradish prepared
481. Hot dog all beef
482. Hummus
483. Ice (frozen water)
484. Ice cream chocolate
485. Ice cream strawberry
486. Ice cream vanilla
487. Ice cubes
488. Iced tea black unsweetened
489. Irish coffee with alcohol and whipped cream
490. Italian bread
491. Jackfruit raw
492. Jams and preserves
493. Jellies
494. Jicama raw
495. Kale raw
496. Ketchup or catsup
497. Kidney beans boiled without salt
498. Kidney beans canned
499. Kidney beans raw
500. Kiwi fruit raw
501. Kohlrabi raw
502. Kosher salt
503. Kumquats raw
504. Lamb cuts lean and fat trimmed to 1/4" raw
505. Lamb leg boneless lean and fat trimmed to 1/8" fat
506. Lamb loin chop New Zealand lean meat and fat raw
507. Lard or pig fat
508. Leeks raw
509. Lemon juice canned or bottled
510. Lemon juice raw
511. Lemon peel or zest raw
512. Lemon pepper seasoning
513. Lemon pepper seasoning salt free
514. Lemon raw
515. Lemongrass raw
516. Lentils French green raw
517. Lentils black beluga raw
518. Lentils boiled without salt
519. Lentils raw
520. Lettuce green leaf raw
521. Lettuce iceberg raw
522. Lettuce raw (butterhead boston or bibb type)
523. Lettuce red leaf raw
524. Lettuce romaine raw
525. Lima beans large boiled without salt
526. Lima beans large canned
527. Lime juice
528. Lime peel or zest raw
529. Limes raw
530. Liqueur
531. Liqueur chocolate
532. Lobster northern cooked moist heat
533. Lobster northern raw
534. Longan fruit dried
535. Longans raw
536. Lotus seeds dried
537. Lychees or litchis raw
538. Macadamias dry roasted with salt
539. Macadamias dry roasted without salt
540. Macadamias raw
541. Mackerel canned drained boneless
542. Madeira wine
543. Mai tai cocktail
544. Mango raw
545. Mango sweetened dried
546. Manhattan cocktail
547. Maple sugar
548. Maple syrup
549. Margarine regular soft salted
550. Margarine regular stick salted
551. Margarita cocktail frozen
552. Margarita on the rocks
553. Marinara or spaghetti sauce
554. Marinara or spaghetti sauce low sodium
555. Marmalade orange
556. Martini
557. Mayonnaise fat free or nonfat
558. Mayonnaise light or lite
559. Mayonnaise regular
560. Mayonnaise with olive oil reduced fat
561. Mexican blend cheese
562. Mexican blend cheese reduced fat
563. Milk canned condensed sweetened
564. Milk canned evaporated nonfat
565. Milk canned evaporated whole
566. Milk chocolate
567. Milk low fat 1% milkfat
568. Milk nonfat skim or fat free
569. Milk reduced fat 2% milkfat
570. Milk whole 3.25% milkfat
571. Mint (all varieties) dried
572. Mint fresh or raw herb
573. Miso
574. Molasses
575. Monterey cheese
576. Monterey cheese low fat
577. Mozzarella cheese fresh
578. Mozzarella cheese part skim low moisture
579. Mozzarella cheese whole milk
580. Mozzarella string cheese
581. Mozzarella string cheese light
582. Muenster cheese
583. Muenster cheese low fat
584. Muesli dry uncooked
585. Mulberries raw
586. Multigrain bread
587. Mung beans raw
588. Mung beans sprouted canned
589. Mung beans sprouted raw
590. Mushrooms brown high vitamin D raw
591. Mushrooms brown raw
592. Mushrooms enoki raw
593. Mushrooms maitake raw
594. Mushrooms morel raw
595. Mushrooms oyster raw
596. Mushrooms portabella high vitamin D raw
597. Mushrooms portabella raw
598. Mushrooms shiitake dried
599. Mushrooms shiitake raw
600. Mushrooms white high vitamin D raw
601. Mushrooms white raw
602. Mushrooms white stir fried
603. Mussels blue raw
604. Mustard dijon
605. Mustard greens raw
606. Mustard seed ground
607. Mustard whole grain
608. Mustard yellow prepared
609. Naan bread
610. Naan whole wheat bread
611. Natto
612. Nectarines raw
613. Neufchatel cheese
614. Noncaloric Sweetener Splenda or Sucralose
615. Noncaloric sweetener Equal or aspartame (blue packet)
616. Noncaloric sweetener Sweet n Low or saccharin (pink packet)
617. Noncaloric sweetener stevia leaf (green packet)
618. Noodles Japanese soba dry uncooked
619. Noodles chinese chow mein
620. Noodles egg cooked with salt
621. Noodles egg cooked without salt
622. Noodles egg dry uncooked
623. Noodles rice dry uncooked
624. Nougat
625. Nougat with nuts, homemade
626. Nougat, homemade
627. Nutmeg ground
628. Nutritional yeast seasoning
629. Oat bran dry uncooked
630. Oat milk lowfat fortified
631. Oat milk unsweetened
632. Oat milk yogurt plain
633. Oatmeal or rolled oats cooked with salt
634. Oatmeal or rolled oats cooked without salt
635. Oatmeal or rolled oats instant fortified dry uncooked
636. Oatmeal or rolled oats regular or quick dry uncooked
637. Octopus raw
638. Okra frozen unprepared
639. Okra raw
640. Old fashioned cocktail
641. Olive or extra virgin olive oil
642. Olives black canned jumbo and super-colossal
643. Olives black canned small to extra large
644. Olives green pickled canned or bottled
645. Olives kalamata pitted
646. Onion flakes dehydrated
647. Onion powder
648. Onions frozen chopped unprepared
649. Onions green spring or scallions raw
650. Onions raw
651. Onions red raw
652. Onions sweet raw
653. Orange juice raw
654. Orange peel or zest raw
655. Oranges mandarin or tangerines canned in juice
656. Oranges mandarin or tangerines raw
657. Oranges raw
658. Oregano dried
659. Oyster Pacific raw
660. Oyster eastern farmed raw
661. Oyster eastern wild cooked moist heat
662. Oyster eastern wild raw
663. Oyster sauce
664. Palm kernel oil
665. Palm oil
666. Papayas raw
667. Paprika
668. Paprika Hungarian
669. Paprika smoked
670. Paratha whole wheat bread
671. Parmesan cheese grated
672. Parmesan cheese grated reduced fat
673. Parmesan cheese hard
674. Parmesan cheese shredded
675. Parsley dried
676. Parsley fresh or raw herb
677. Parsnips boiled without salt
678. Parsnips raw
679. Passion fruit raw
680. Pasta corn cooked without salt
681. Pasta corn dry uncooked
682. Pasta white cooked without salt
683. Pasta white dry uncooked
684. Pasta whole wheat cooked without salt
685. Pasta whole wheat dry uncooked
686. Peaches canned in juice not drained
687. Peaches dried
688. Peaches frozen sliced sweetened
689. Peaches raw
690. Peanut butter chunky with salt
691. Peanut butter chunky without salt
692. Peanut butter smooth with salt
693. Peanut butter smooth without salt
694. Peanut oil
695. Peanuts dry roasted with salt
696. Peanuts dry roasted without salt
697. Peanuts oil roasted with salt
698. Peanuts oil roasted without salt
699. Peanuts raw
700. Pears Asian raw
701. Pears dried
702. Pears raw
703. Pecans dry roasted with salt
704. Pecans dry roasted without salt
705. Pecans oil roasted with salt
706. Pecans oil roasted without salt
707. Pecans raw
708. Pepper black
709. Pepper poblano raw
710. Pepper red or cayenne spice
711. Pepper white
712. Peppermint extract
713. Peppers chili green canned
714. Peppers hot green chili raw
715. Peppers hot pickled canned
716. Peppers hot red chili raw
717. Peppers jalapeno raw
718. Peppers serrano raw
719. Peppers sweet green raw
720. Peppers sweet red raw
721. Peppers sweet yellow raw
722. Persimmons Japanese raw
723. Persimmons raw
724. Pesto prepared refrigerated
725. Pickle relish hot dog
726. Pickle relish sweet
727. Pickles dill cucumber
728. Pickles sour cucumber
729. Pickles sweet cucumber
730. Pie crust baked from dry mix
731. Pie crust baked from frozen
732. Pie crust baked from refrigerated
733. Pie crust chocolate cookie type
734. Pie filling apple canned
735. Pie filling blueberry canned
736. Pie filling cherry canned
737. Pine nuts raw
738. Pineapple canned in juice
739. Pineapple chunks frozen
740. Pineapple juice canned or bottled
741. Pineapple juice prepared from frozen concentrate
742. Pineapple raw
743. Pinto beans boiled without salt
744. Pinto beans canned
745. Pinto beans raw
746. Pistachios dry roasted with salt
747. Pistachios dry roasted without salt
748. Pistachios raw
749. Pita white
750. Pita whole wheat
751. Plantains raw
752. Plums dried or prunes
753. Plums raw
754. Polenta dry uncooked
755. Polenta precooked tube
756. Pollock Atlantic cooked dry heat
757. Pollock Atlantic raw
758. Pollock alaska raw
759. Pomegranate juice bottled
760. Pomegranates raw
761. Popcorn air popped
762. Popcorn dry unpopped uncooked
763. Popcorn oil popped
764. Poppy seeds or poppyseeds
765. Pork bacon Canadian unprepared
766. Pork bacon cooked pan fried
767. Pork bacon reduced sodium cooked
768. Pork bacon reduced sodium unprepared
769. Pork bacon unprepared
770. Pork ground 79% lean 21% fat raw
771. Pork ground 84% lean 16% fat raw
772. Pork liver raw
773. Pork loin center chop bone-in lean meat and fat raw
774. Pork loin ribs lean meat only raw
775. Pork loin top roast boneless raw
776. Pork sausage Italian raw
777. Pork sausage Polish
778. Pork sausage chorizo link or ground raw
779. Pork sausage link or ground cooked
780. Pork sausage smoked andouille
781. Pork shoulder boneless lean and fat raw
782. Pork tenderloin lean meat and fat raw
783. Pork top loin chops boneless lean meat and fat raw
784. Pork top loin chops boneless lean meat only raw
785. Port de salut cheese
786. Port wine
787. Potato flour
788. Potatoes baked with skin without salt
789. Potatoes boiled with skin without salt
790. Potatoes hashed brown frozen plain prepared
791. Potatoes with skin raw
792. Prickly pear cactus or nopal raw
793. Processed American cheese
794. Processed Swiss cheese
795. Provolone cheese
796. Provolone cheese reduced fat
797. Psyllium fiber all natural
798. Pummelo raw
799. Pumpkin canned with salt
800. Pumpkin canned without salt
801. Pumpkin pie spice
802. Pumpkin raw
803. Pumpkin seed kernels (shelled) dried
804. Pumpkin seed kernels (shelled) raw
805. Pumpkin seed kernels (shelled) roasted with salt
806. Pumpkin seed kernels (shelled) roasted without salt
807. Pumpkin seeds whole with shell roasted with salt
808. Pumpkin seeds whole with shell roasted without salt
809. Queso blanco cheese
810. Queso cotija cheese
811. Queso fresco cheese
812. Queso seco cheese
813. Quinces raw
814. Quinine water
815. Quinine water diet
816. Quinoa cooked without salt
817. Quinoa uncooked
818. Radishes oriental raw
819. Radishes raw
820. Raisin bread
821. Raisins golden seedless
822. Raisins seedless
823. Raspberries frozen unsweetened
824. Raspberries raw
825. Red potatoes with skin raw
826. Red sangria
827. Red table wine
828. Refried beans traditional canned
829. Refried beans vegetarian canned
830. Rhine wine
831. Rhubarb frozen uncooked
832. Rhubarb raw
833. Rice bran oil
834. Rice brown instant cooked without salt
835. Rice brown long grain cooked without salt
836. Rice brown long grain dry uncooked
837. Rice brown medium grain cooked without salt
838. Rice brown medium grain dry uncooked
839. Rice flour brown
840. Rice flour white
841. Rice milk unsweetened fortified
842. Rice white cooked without salt
843. Rice white glutinous cooked without salt
844. Rice white glutinous dry uncooked
845. Rice white long grain cooked with salt
846. Rice white long grain cooked without salt
847. Rice white long grain dry uncooked
848. Rice white medium grain dry uncooked
849. Rice white short grain cooked without salt
850. Rice white short grain dry uncooked
851. Rice wild cooked without salt
852. Rice wild dry uncooked
853. Ricotta cheese nonfat
854. Ricotta cheese part skim milk
855. Ricotta cheese whole milk
856. Roast beef from deli
857. Rolls dinner white
858. Rolls dinner whole wheat
859. Rolls french
860. Rolls hard or Kaiser
861. Romano cheese
862. Roquefort cheese
863. Rosemary dried
864. Rosemary fresh or raw herb
865. Rotisserie chicken breast meat only skinless
866. Rotisserie chicken thigh meat only skinless
867. Rotisserie chicken wing meat only skinless
868. Rum punch
869. Russet potatoes with skin raw
870. Russian tea
871. Rutabagas boiled without salt
872. Rutabagas raw
873. Rye bread
874. Rye flour dark
875. Sablefish smoked
876. Safflower oil
877. Sage ground
878. Salad dressing Greek
879. Salad dressing blue or roquefort cheese
880. Salad dressing blue or roquefort cheese reduced calorie
881. Salad dressing caesar regular
882. Salad dressing coleslaw
883. Salad dressing coleslaw reduced fat
884. Salad dressing french fat-free
885. Salad dressing french reduced fat
886. Salad dressing french regular
887. Salad dressing italian
888. Salad dressing italian fat-free
889. Salad dressing ranch fat-free
890. Salad dressing ranch regular
891. Salad dressing russian
892. Salad dressing russian low calorie
893. Salad dressing sesame seed regular
894. Salad dressing thousand island fat-free
895. Salad dressing thousand island reduced fat
896. Salad dressing thousand islands
897. Salmon Atlantic wild cooked dry heat
898. Salmon Atlantic wild raw
899. Salmon atlantic farmed raw
900. Salmon chinook raw
901. Salmon chinook smoked
902. Salmon chinook smoked lox
903. Salmon pink canned drained solids with bone
904. Salmon pink cooked dry heat
905. Salmon pink raw
906. Salmon sockeye raw
907. Salsa
908. Salsa verde
909. Salt
910. Sardines canned in oil drained solids with bone
911. Sardines canned in tomato sauce drained solids with bone
912. Sauterne wine
913. Scallops cooked steamed
914. Scallops raw
915. Screwdriver cocktail
916. Sea bass mixed species raw
917. Sea salt iodized
918. Sea salt non-iodized
919. Seaweed Nori dried
920. Seaweed kelp raw
921. Seaweed laver raw
922. Seaweed spirulina dried
923. Seaweed spirulina raw
924. Seaweed wakame raw
925. Seltzer water
926. Sesame butter or tahini
927. Sesame oil
928. Sesame seed kernels (shelled) dried
929. Sesame seed kernels (shelled) toasted with salt
930. Sesame seed kernels (shelled) toasted without salt
931. Shallots freeze-dried
932. Shallots raw
933. Shirataki noodles
934. Shrimp cooked no added fat
935. Shrimp raw
936. Shrimp raw frozen medium peeled and deveined tail off
937. Snails raw
938. Snapper mixed species raw
939. Snow peas or sugar snap peas raw
940. Snowpeas or sugar snap peas boiled without salt
941. Sofrito sauce homemade
942. Soup cream of chicken canned condensed
943. Soup cream of mushroom canned, condensed
944. Soup onion mix dehydrated dry form
945. Southern comfort
946. Soy milk unsweetened fortified
947. Soy milk unsweetened high protein
948. Soy milk vanilla fortified
949. Soy sauce
950. Soy sauce reduced sodium
951. Soy yogurt plain fortified
952. Soybean oil
953. Spaghetti whole wheat cooked without salt
954. Spaghetti with pesto sauce
955. Spaghetti with pesto sauce and meat
956. Spices anise seed
957. Spices caraway seed
958. Spices celery seed
959. Spices dry taco seasoning mix
960. Spices fenugreek seed
961. Spices poultry seasoning
962. Spinach all varieties raw
963. Spinach cooked boiled drained without salt
964. Spinach frozen unprepared
965. Split peas boiled without salt
966. Split peas raw
967. Squash acorn raw
968. Squash butternut baked without salt
969. Squash butternut frozen boiled without salt
970. Squash butternut frozen unprepared
971. Squash butternut raw
972. Squash spaghetti cooked without salt
973. Squash spaghetti raw
974. Squash summer all types cooked without salt
975. Squash summer all types raw
976. Squash winter all types cooked without salt
977. Squash winter all types raw
978. Squid raw
979. Sriracha or hot chile sauce
980. Starfruit or carambola raw
981. Steak sauce
982. Strawberries frozen unsweetened
983. Strawberries raw
984. Sugar powdered or confectioners sugar
985. Sugar turbinado
986. Sugar white
987. Sugar white baking blend (sucralose and sugar)
988. Sumac spice
989. Sunflower oil
990. Sunflower seed butter with salt
991. Sunflower seed butter without salt
992. Sunflower seed kernels (shelled) dried
993. Sunflower seed kernels (shelled) dry roasted with salt
994. Sunflower seed kernels (shelled) dry roasted without salt
995. Sunflower seed kernels (shelled) oil roasted with salt
996. Sunflower seed kernels (shelled) oil roasted without salt
997. Surimi imitation crab
998. Sweet potato baked with skin without salt
999. Sweet potato raw
1000. Swiss chard boiled without salt
1001. Swiss chard raw
1002. Swiss cheese
1003. Swiss cheese low fat
1004. Swiss cheese nonfat or fat free
1005. Sylvaner wine
1006. Tabasco sauce
1007. Taco shells baked
1008. Tamari sauce
1009. Tamari sauce reduced sodium
1010. Tamarinds raw
1011. Taro raw
1012. Tea black decaf prepared without milk or sugar
1013. Tea black regular instant powder unsweetened
1014. Tea black regular prepared without milk or sugar
1015. Tea chamomile prepared without milk or sugar
1016. Tea green decaf prepared without milk or sugar
1017. Tea green regular prepared without milk or sugar
1018. Tea herbal not chamomile prepared without milk or sugar
1019. Tempeh cooked
1020. Tempeh uncooked
1021. Teriyaki sauce
1022. Teriyaki sauce reduced sodium
1023. Thai peanut sauce
1024. Thyme dried
1025. Thyme fresh or raw herb
1026. Tilapia cooked dry heat
1027. Tilapia raw
1028. Tilsit cheese
1029. Toasted white bread
1030. Toasted whole wheat bread
1031. Tofu crumbles
1032. Tofu extra firm made with nigari
1033. Tofu firm made with calcium sulfate
1034. Tofu firm made with nigari
1035. Tofu regular made with calcium sulfate
1036. Tofu soft made with nigari
1037. Tofu soft silken
1038. Tokaji wine
1039. Tom Collins cocktail
1040. Tomatillos raw
1041. Tomato juice
1042. Tomato juice low sodium
1043. Tomato paste canned
1044. Tomato paste canned no salt added
1045. Tomato powder
1046. Tomato puree
1047. Tomato puree canned no salt added
1048. Tomato sauce canned
1049. Tomato sauce canned no salt added
1050. Tomatoes cherry raw
1051. Tomatoes crushed canned
1052. Tomatoes crushed canned no salt added
1053. Tomatoes diced canned
1054. Tomatoes diced canned no salt added
1055. Tomatoes green raw
1056. Tomatoes orange raw
1057. Tomatoes red raw
1058. Tomatoes sun dried or sundried
1059. Tomatoes sun dried or sundried packed in oil
1060. Tomatoes whole canned
1061. Tomatoes whole canned no salt added
1062. Tomatoes whole stewed canned
1063. Tomatoes yellow raw
1064. Tortilla chips
1065. Tortilla white flour low carb
1066. Tortillas corn
1067. Tortillas white flour
1068. Tortillas white flour low sodium
1069. Tortillas whole wheat flour
1070. Tortillas whole wheat flour low carb
1071. Tostada shells corn
1072. Traminer wine
1073. Tuna bluefin raw
1074. Tuna light canned in oil
1075. Tuna light canned in water
1076. Tuna white albacore canned in oil
1077. Tuna white albacore canned in water
1078. Tuna yellowfin cooked dry heat
1079. Tuna yellowfin raw
1080. Turkey bacon low sodium unprepared
1081. Turkey bacon unprepared
1082. Turkey dark meat only skinless roasted
1083. Turkey drumstick meat and skin raw
1084. Turkey drumstick roasted meat and skin
1085. Turkey ground 85% lean 5% fat raw
1086. Turkey ground 93% lean 7% fat raw
1087. Turkey sausage Italian smoked
1088. Turkey sausage raw
1089. Turmeric ground
1090. Turnip greens raw
1091. Turnips boiled without salt
1092. Turnips raw
1093. Vanilla extract
1094. Vanilla imitation extract
1095. Veal cutlet boneless raw
1096. Veal cuts lean only raw
1097. Veal ground raw
1098. Veal or calf liver cooked pan fried
1099. Vegan butter spread
1100. Vegan mayonnaise regular
1101. Vegan mozzarella cheese shredded
1102. Vegan parmesan cheese
1103. Vegetable broth
1104. Vegetable broth or bouillon low sodium
1105. Vegetable juice cocktail
1106. Vegetable juice cocktail low sodium
1107. Vegetable oil
1108. Vermouth dry
1109. Vermouth sweet
1110. Vinegar cider
1111. Vinegar red wine
1112. Vinegar rice
1113. Vinegar white distilled
1114. Vinegar white wine
1115. Vital wheat gluten
1116. Walnut oil
1117. Walnuts dry roasted with salt
1118. Walnuts glazed
1119. Walnuts raw
1120. Water
1121. Watercress raw
1122. Watermelon raw
1123. Watermelon seed kernels (shelled) dried
1124. Wheat germ oil
1125. White bread
1126. White table wine
1127. Whitefish smoked
1128. Whole wheat bread
1129. Wine cooler
1130. Wonton or egg roll wrappers
1131. Worcestershire sauce
1132. Worcestershire sauce vegan
1133. Xanthan gum
1134. Xylitol granulated sweetener
1135. Yam boiled or baked without salt
1136. Yam raw
1137. Yogurt plain fat free or nonfat
1138. Yogurt plain low fat
1139. Yogurt plain whole milk
1140. Za'atar or zaatar spice blend
1141. Zucchini boiled without salt
1142. Zucchini raw

IMPORTANT: If you cannot find a suitable match in the MyNetDiary list for a visible ingredient, 
choose the closest available option or omit that ingredient rather than creating a custom name.


DISH DECOMPOSITION RULE:
When you encounter complex dish names with multiple components connected by "and", "with", "plus", "alongside", etc., you MUST break them down into separate individual dishes.

NUTRITIONAL COMPLETENESS REQUIREMENTS:
For EACH dish, list ALL PRIMARY INGREDIENTS that materially contribute to nutrition calculations (protein, carbohydrate, fat sources, sauces, cooking oils, etc.):
• The goal is to avoid omitting any ingredient that would significantly affect calorie or macro-nutrient totals.
• This exhaustive ingredient list is critical because downstream nutrition calculation logic relies on having every significant component represented in the query set.
• ALL ingredient names MUST be selected from the MyNetDiary list provided above.

WEIGHT ESTIMATION REQUIREMENTS (MANDATORY):
For EACH ingredient, you MUST estimate the weight in grams (weight_g) based on visual analysis:
• This field is MANDATORY - the system will fail if any ingredient lacks weight_g
• Analyze the portion size, volume, and visual density of each ingredient in the photo
• Consider typical serving sizes and food density for accurate weight estimation
• Use visual cues like plate size, utensils, or other reference objects for scale
• For liquids: estimate volume and convert to weight (1ml ≈ 1g for most beverages)
• For solids: consider the 3D volume and typical density of the food item
• Provide realistic weights that reflect what is actually visible in the image
• Weight estimates should be practical and achievable (e.g., 50-200g for main ingredients, 5-30g for seasonings/sauces)
• NEVER omit the weight_g field - it is required for every single ingredient

PLATE-BASED VISUAL WEIGHT ESTIMATION:
• Carefully observe the plate/bowl size, shape, and depth in the image
• Use the plate as your primary reference for scale - standard dinner plates are typically 25-28cm (10-11 inches) diameter
• Estimate how much of the plate/bowl is covered by each ingredient and at what depth/height
• Consider the 3D volume: height/thickness of food items relative to the plate rim
• For pasta/rice: estimate the volume they occupy in the bowl/plate and convert to weight (cooked pasta ~1.1g/ml, cooked rice ~1.5g/ml)
• For salads: consider the leaf density and compression - loose greens are ~0.2-0.3g/ml, compressed ~0.5g/ml
• For sauces/dressings: observe the coverage area and estimated thickness on the plate
• Cross-reference your estimates: does the total weight seem reasonable for what's visible on the plate?
• If multiple dishes are present, compare their relative sizes to ensure proportional weight estimates

AMERICAN PORTION SIZE CONTEXT:
• Assume this is a typical American meal serving - American portions are generally 25-50% larger than international standards
• Restaurant portions in America are typically generous and designed to provide satisfaction and value
• Main dishes (pasta, rice, meat) should reflect American restaurant/dining portion sizes
• For pasta dishes: American restaurant servings are typically 200-300g cooked weight (equivalent to 80-120g dry)
• For proteins: American servings are typically 150-250g (6-8 oz)
• For side salads: American portions are typically 100-200g of greens
• Consider that American dining culture emphasizes generous portions and hearty meals

CRITICAL COOKING STATE CONSIDERATION:
For ingredients like pasta, rice, grains, and legumes that absorb significant water during cooking:
• ALWAYS specify the cooking state in the ingredient_name (e.g., "pasta white dry uncooked" vs "pasta white cooked")
• Be extremely careful about weight estimation - cooked vs uncooked has dramatically different nutrition per gram
• Cooked pasta/rice typically weighs 2-3x more than dry due to water absorption, but nutrition per gram is 2-3x LESS
• When you see cooked pasta/rice in the image, estimate the COOKED weight, but ensure ingredient_name reflects "cooked" state
• For dry ingredients that appear cooked: estimate what the dry weight would have been before cooking
• This distinction is CRITICAL for accurate nutrition calculation - getting this wrong can cause 200-300% calorie errors

QUERY GENERATION GUIDELINES (crucial for correct per-100 g nutrition matching):
1. For ingredients: ONLY use names from the MyNetDiary list above - NO custom names allowed
2. For dish names: Use simple, searchable names that exist as separate database entries
3. Avoid overly generic or misleading single-word queries
4. When a cooking or preservation method materially changes nutrition, include it
5. Output MUST be in English
6. Do NOT include quantities, units, brand marketing slogans, or flavour adjectives

CRITICAL FINAL VERIFICATION STEP:
Before finalizing your response, you MUST perform a strict verification check:
• Go through EVERY SINGLE ingredient name in your response
• Verify that each ingredient name appears EXACTLY as written in the MyNetDiary ingredient list provided above
• Check for exact spelling, capitalization, and word order matches
• If ANY ingredient name does not match EXACTLY, you MUST replace it with the correct name from the list
• If no exact match exists, choose the closest available option from the MyNetDiary list
• This verification is MANDATORY - ingredient names that don't match exactly will cause system failures

-------------------------------------------------------------
JSON RESPONSE STRUCTURE
-------------------------------------------------------------
Return a JSON object with the following structure:

{
  "dishes": [
    {
      "dish_name": "string",
      "confidence": 0.0-1.0,
      "ingredients": [
        {
          "ingredient_name": "string (MUST be EXACT match from MyNetDiary list - verify before submitting)",
          "weight_g": "number (MANDATORY - estimated weight in grams based on visual analysis)",
          "confidence": 0.0-1.0
        }
      ]
    }
  ]
}

REMINDER: After completing your JSON response, perform a final verification that every "ingredient_name" value matches EXACTLY with an entry in the MyNetDiary ingredient list provided above.
```

### User Prompt

**タイムスタンプ**: 2025-09-14T09:21:51.499151

```
Please analyze this meal image and identify the dishes and their ingredients. For ingredients, you MUST select ONLY from the provided MyNetDiary ingredient list - do not create custom ingredient names. CRITICALLY IMPORTANT: You MUST estimate the weight in grams (weight_g) for EVERY SINGLE ingredient - this field is mandatory and the system will fail if any ingredient lacks weight_g. Base your weight estimates on visual analysis of portion sizes, volumes, and typical food densities. Use visual cues like plate size, utensils, or reference objects for scale. Focus on providing clear, searchable dish names for nutrition database queries. Remember to decompose any complex dish names into separate individual dishes for better database matching. FINAL STEP: Before submitting your response, double-check that EVERY ingredient name in your JSON response matches EXACTLY with the names in the MyNetDiary ingredient list provided - this verification is critical for system functionality.
```

**変数**:
- optional_text: None
- image_mime_type: image/jpeg

## AI推論の詳細

