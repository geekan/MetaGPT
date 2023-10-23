% 定义元素
y1 = {[1, 1, 4, 4, 4, 4, 5, 13, 13, 14, 15, 17, 19, 19, 22, 22, 23, 23, 24, 24, 24, 24, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26]; 
      [1, 1, 1, 1, 4, 4, 4, 4, 9, 9, 9, 12, 12, 13, 13, 15, 16, 16, 16, 16, 19, 20, 20, 20, 21, 22, 24, 24, 24, 24, 25, 27, 27, 27, 27, 31, 31, 31];
      [1, 1, 2, 3, 4, 4, 4, 4, 4, 4, 4, 9, 10, 11, 12, 12, 13, 14, 14, 15, 16, 16, 17, 18, 19, 20, 20, 20, 20, 20, 21, 23, 24, 24, 27, 27, 27, 27, 27, 27, 28, 28, 28, 28, 28, 29, 30, 30, 32, 32, 33, 34, 34, 34, 34, 37, 37];
      [0, 1, 1, 3, 4, 4, 8, 9, 9, 9, 10, 10, 11, 11, 14, 17, 17, 17, 17, 18, 18, 18, 18, 18, 18, 18, 20, 20, 20, 20, 23, 24, 25, 27, 30, 30, 30, 30, 30, 30, 30, 30, 30, 35, 35, 35, 35, 35, 35, 35, 35, 35, 35, 36, 38, 38, 38, 38, 38, 39, 39, 39, 39, 39, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42];
      [1, 1, 1, 2, 5, 7, 8, 9, 9, 9, 9, 9, 10, 12, 13, 14, 14, 15, 16, 17, 17, 18, 19, 20, 22, 23, 23, 23, 23, 23, 23, 23, 23, 24, 24, 25, 25, 26, 27, 29, 29, 29, 29, 29, 29, 29, 29, 29, 32, 32, 32, 32, 37, 37, 37, 37, 37, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 40, 40, 40, 40, 41, 42, 42];
      [1, 1, 1, 2, 3, 3, 3, 3, 5, 6, 6, 8, 9, 10, 10, 12, 12, 12, 12, 12, 12, 13, 14, 15, 17, 18, 19, 20, 20, 21, 22, 22, 23, 24, 25, 27, 27, 28]};
x = {1:1:33;1:1:38;1:1:57;1:1:82;1:1:81;1:1:38};

% 创建共享的x向量
shared_x = 0:1:max(cellfun(@max,x));

% 拆分y1和x
y1_MetaGPT = y1(1:4);
x_MetaGPT = x(1:4);
y1_Voyager = y1(5:6);
x_Voyager = x(5:6);

% 插值和计算上下限
interp_y1_MetaGPT = cellfun(@(y, x) interp1(x, y, shared_x, 'linear', 'extrap'), y1_MetaGPT, x_MetaGPT, 'UniformOutput', false);
minY_MetaGPT = min(cell2mat(interp_y1_MetaGPT));
maxY_MetaGPT = max(cell2mat(interp_y1_MetaGPT));

interp_y1_Voyager = cellfun(@(y, x) interp1(x, y, shared_x, 'linear', 'extrap'), y1_Voyager, x_Voyager, 'UniformOutput', false);
minY_Voyager = min(cell2mat(interp_y1_Voyager));
maxY_Voyager = max(cell2mat(interp_y1_Voyager));

% 计算均值
meanY_MetaGPT = mean(cell2mat(interp_y1_MetaGPT));
meanY_Voyager = mean(cell2mat(interp_y1_Voyager));

% 绘图
figure
hold on

% 绘制MetaGPT的均值曲线，颜色设为蓝色
h1=plot(shared_x, meanY_MetaGPT, 'b', 'LineWidth', 2);

% 绘制MetaGPT的上下限范围，颜色设为蓝色
h2=fill([shared_x, fliplr(shared_x)], [minY_MetaGPT, fliplr(maxY_MetaGPT)], 'b', 'FaceAlpha', 0.2, 'EdgeColor', 'none');

% 绘制Voyager的均值曲线，颜色设为红色
h3=plot(shared_x, meanY_Voyager, 'r', 'LineWidth', 2);

% 绘制Voyager的上下限范围，颜色设为红色
h4=fill([shared_x, fliplr(shared_x)], [minY_Voyager, fliplr(maxY_Voyager)], 'r', 'FaceAlpha', 0.2, 'EdgeColor', 'none');

% 绘制MetaGPT的每一条曲线
for i = 1:length(y1_MetaGPT)
    plot(x_MetaGPT{i}, y1_MetaGPT{i}, 'b--'); % 使用蓝色虚线
end

% 绘制Voyager的每一条曲线
for i = 1:length(y1_Voyager)
    plot(x_Voyager{i}, y1_Voyager{i}, 'r--'); % 使用红色虚线
end

% 设置坐标轴范围和标签
xlim([0 35]) % x轴范围设为最大的x值
ylim([0 35])
xlabel('# of Rounds')
ylabel('Total Variety of Items Collected')

% 设置标题和图例（假设每条线代表一个方法）
legend([h1,h2,h3,h4],'MetaGPT Mean','MetaGPT Range', 'Voyager Mean','Voyager Range')

hold off
