# 解决 Azure 配额超限问题

## ❌ **当前问题**
- **错误**: Error 403 - This web app is stopped
- **状态**: QuotaExceeded 
- **原因**: Azure 免费层配额用完

## 🔍 **Azure 免费层限制**

### **App Service 免费层限制：**
- ✅ **每月计算时间**: 60分钟
- ✅ **App Service Plan**: 只能有1个免费的
- ✅ **存储空间**: 1GB
- ✅ **带宽**: 每天165MB

## 🛠️ **解决方案**

### **方案 1: 删除其他资源组中的 App Service**

1. **登录 Azure Portal**: https://portal.azure.com

2. **检查所有 App Service Plans**:
   - 搜索 "App Service plans"
   - 查看是否有多个免费层的 App Service Plan
   - 删除不需要的 App Service Plan

3. **检查这些资源组**:
   - `DefaultResourceGroup-CCAN`
   - `DefaultResourceGroup-EUS` 
   - `DefaultResourceGroup-canadacentral`
   - `ResourceMoverRG-eastus2-eastus-eus2`

4. **删除不需要的资源**:
   - 如果有其他 Web Apps 不再需要，请删除它们
   - 保留我们的 `cst8919-assignment1` 资源组

### **方案 2: 重启当前应用** 

如果没有其他冲突资源，尝试重启：

```bash
# 在新终端中运行
az webapp start --resource-group cst8919-assignment1 --name cst8919-flask-auth0-1751376574
```

### **方案 3: 升级到付费计划** (如果需要)

```bash
# 升级到 Basic B1 计划 (约 $13/月)
az appservice plan update \
    --name cst8919-plan \
    --resource-group cst8919-assignment1 \
    --sku B1
```

## 🚨 **立即行动步骤**

### **步骤 1: 清理不需要的资源**
1. 访问 https://portal.azure.com
2. 搜索 "Resource groups"
3. 检查每个资源组：
   - `DefaultResourceGroup-CCAN`
   - `DefaultResourceGroup-EUS`
   - `DefaultResourceGroup-canadacentral`
4. 删除不需要的 App Services 和 App Service Plans

### **步骤 2: 重启应用**
在新终端中执行：
```bash
cd /Users/here/Documents/CST8919/lab3/flask-auth0-clean
az webapp start --resource-group cst8919-assignment1 --name cst8919-flask-auth0-1751376574
```

### **步骤 3: 检查状态**
```bash
az webapp show --resource-group cst8919-assignment1 --name cst8919-flask-auth0-1751376574 --query "state" --output tsv
```

### **步骤 4: 如果仍然失败**
考虑升级到 Basic 计划：
```bash
az appservice plan update --name cst8919-plan --resource-group cst8919-assignment1 --sku B1
```

## ✅ **成功后的验证**

1. **访问应用**: https://cst8919-flask-auth0-1751376574.azurewebsites.net
2. **检查状态**: 应该显示 "Running"
3. **测试登录**: 确保 Auth0 集成正常工作

## 💡 **预防措施**

1. **定期清理**: 删除不需要的 Azure 资源
2. **监控使用量**: 在 Azure Portal 中检查配额使用情况
3. **设置警报**: 为接近配额限制设置通知

## 🔗 **相关链接**

- [Azure 免费账户限制](https://azure.microsoft.com/en-us/pricing/free-services/)
- [App Service 定价](https://azure.microsoft.com/en-us/pricing/details/app-service/windows/)
- [Azure Portal](https://portal.azure.com)

---

**重要**: 完成清理后，一定要重新设置环境变量（按照 `azure-manual-config.md` 指南）并重启应用！ 